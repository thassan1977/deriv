package com.deriv.frauddetect.service;

import com.deriv.frauddetect.domain.*;
import com.deriv.frauddetect.entity.FraudCase;
import com.deriv.frauddetect.enums.CaseStatus;
import com.deriv.frauddetect.repository.FraudCaseRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.*;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class FraudStreamProcessor {

    private final RedisTemplate<String, String> redisTemplate;
    private final FraudCaseRepository fraudCaseRepository;
    private final ObjectMapper objectMapper;
    private final FraudAlertService alertService;
    private final TrafficMonitor trafficMonitor;

    private static final String STREAM_KEY = "deriv:transactions";
    private static final String CONSUMER_GROUP = "fraud-detector1";
    private static final String CONSUMER_NAME = "processor-1";
    private static final String AI_QUEUE = "fraud:investigation:queue";
    private long lastCheckTime = System.currentTimeMillis();

    @PostConstruct
    public void initGroup() {
        try {
            redisTemplate.opsForStream().createGroup(STREAM_KEY, ReadOffset.latest(), CONSUMER_GROUP);
//            redisTemplate.opsForStream().createGroup(STREAM_KEY, ReadOffset.from("0"), CONSUMER_GROUP);
            log.info("Consumer group {} created on stream {}", CONSUMER_GROUP, STREAM_KEY);
        } catch (Exception e) {
            log.warn("Group {} may already exist: {}", CONSUMER_GROUP, e.getMessage());
        }
    }

    /**
     * Window-based processing: every 1 minute
     */
    @Scheduled(fixedDelay = 100) // Reduced to 100ms for "near-instant" feel
    public void processWindow() {
        // 1. Check for data
        List<MapRecord<String, Object, Object>> records = redisTemplate
                .opsForStream()
                .read(Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
                        StreamReadOptions.empty().count(1000),
                        StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed()));

        // Keep it quiet when empty to avoid log spam
        if (records == null || records.isEmpty()) {
            return;
        }
        trafficMonitor.increment(records.size());

        log.info("STREAM BATCH: Found {} new transactions to process", records.size());

        List<TransactionEvent> grayArea = new ArrayList<>();

        for (MapRecord<String, Object, Object> record : records) {
            String txId = record.getId().getValue();
            log.info("===================================================");
            log.info("START: Processing Tx ID: {}", txId);
            try {Thread.sleep(500);} catch (Exception e){}
            try {
                TransactionEvent event = parseEvent(record);
                RuleResult result = applyRules(event);
                String caseId = "CASE-" + Instant.now().toEpochMilli();
                event.setCaseId(caseId);
                if (result.isDefinitive()) {
                    log.warn("FRAUD CHECK: Tx {} is DEFINITIVE ({})", txId, result);
                    saveFraudCase(event, result.getDecision());
                } else {
                    log.info("GRAY AREA: Tx {} requires AI investigation", txId);
                    // 1. Generate the Case ID here so you can link it

                    // 2. Save the case to the DB now with status 'PENDING' or 'UNDER_INVESTIGATION'
                    // You might need a method like saveInitialFraudCase(event, caseId)
                    saveFraudCase(event, CaseStatus.UNDER_INVESTIGATION);
                    grayArea.add(event);

                    queueForAIInvestigation(grayArea, caseId);
                }

                // Acknowledge the message so Redis knows we're done
                redisTemplate.opsForStream().acknowledge(STREAM_KEY, CONSUMER_GROUP, record.getId());
                log.info("ACK: Tx {} cleared from stream", txId);

            } catch (Exception e) {
                log.error("ERROR: Failed processing Tx {}: {}", txId, e.getMessage());
            }
        }

        log.info("BATCH COMPLETE: Processed {} records", records.size());
    }


    // ---------------------------
    // Rule Engine
    // ---------------------------
    private RuleResult applyRules(TransactionEvent event) {
        RuleResult result = new RuleResult();

        UserProfile user = event.getUserProfile();
        DeviceProfile device = event.getDeviceProfile();
        IpProfile ip = event.getIpProfile();
        DocumentProfile doc = event.getDocumentProfile();

        // -------------------- Definitive rules --------------------
        if (ip != null && ip.isSanctionedCountry()) {
            result.setDecision(CaseStatus.AUTO_BLOCKED);
            result.setConfidence(BigDecimal.ONE.doubleValue());
            result.addSignal("sanctions_match", "Accessing from sanctioned country");
            return result;
        }

        if (user != null && user.getDeclaredMonthlyIncome() != null && event.getAmount() != null) {
            double declaredIncome = user.getDeclaredMonthlyIncome().doubleValue();
            double amount = event.getAmount().doubleValue();
            if (declaredIncome > 0 && amount > declaredIncome * 15) {
                result.setDecision(CaseStatus.AUTO_BLOCKED);
                result.setConfidence(BigDecimal.valueOf(0.98).doubleValue());
                result.addSignal("income_mismatch",
                        String.format("Deposit %.2f > 1500%% of declared income %.2f", amount, declaredIncome));
                return result;
            }
        }

        // -------------------- Scoring for gray area --------------------
        double riskScore = 0.0;
        Map<String, Object> signals = new HashMap<>();

        if (ip != null && ip.isVpn() && ip.isHighRiskCountry()) {
            riskScore += 0.25;
            signals.put("vpn_detected", true);
        }

        if (device != null && device.getTotalUsersCount() > 5) {
            riskScore += 0.15;
            signals.put("multiple_devices", device.getTotalUsersCount());
        }

        if (hasRapidDepositWithdrawal(event)) {
            riskScore += 0.30;
            signals.put("rapid_churn", true);
        }

        if (doc != null && doc.getConfidenceScore() != null && doc.getConfidenceScore().doubleValue() < 0.7) {
            riskScore += 0.20;
            signals.put("document_issues", doc.getConfidenceScore());
        }

        result.setRiskScore(BigDecimal.valueOf(riskScore).doubleValue());
        result.setSignals(signals);

        // -------------------- Thresholds --------------------
        if (riskScore < 0.15) {
            result.setDecision(CaseStatus.AUTO_APPROVED);
            result.setConfidence(BigDecimal.valueOf(0.95).doubleValue());
        } else if (riskScore > 0.75) {
            result.setDecision(CaseStatus.AUTO_BLOCKED);
            result.setConfidence(BigDecimal.valueOf(0.96).doubleValue());
        } else {
            result.setDecision(CaseStatus.UNDER_INVESTIGATION);
            result.setConfidence(BigDecimal.valueOf(0.50).doubleValue());
        }

        return result;
    }

    // ---------------------------
    // Save Fraud Case
    // ---------------------------
    private void saveFraudCase(TransactionEvent event, CaseStatus status) {
//        FraudCase fc = new FraudCase();
//
//        // Use the ID generated for AI, or create a new one for definitive cases
//        fc.setCaseId(manualCaseId != null ? manualCaseId : "CASE-DEF-" + Instant.now().toEpochMilli());
//        fc.setUserId(event.getUserId());
//        fc.setTriggerTransactionId(event.getTransactionId());
//        fc.setCreatedAt(Instant.now());
//        fc.setUpdatedAt(Instant.now());
//        fc.setTriggeredBy("RULE_ENGINE");
//
//        // Logic Switch: If result is definitive, use its status; else, mark as pending
//        if (result.isDefinitive()) {
//            fc.setStatus(result.getDecision()); // e.g. AUTO_BLOCKED
//            fc.setFraudProbability(BigDecimal.valueOf(result.getConfidence()));
//            fc.setAiReasoning("Definitive rule match. No AI escalation required.");
//        } else {
//            fc.setStatus("UNDER_INVESTIGATION");
//            fc.setFraudProbability(BigDecimal.valueOf(result.getRiskScore()));
//            fc.setAiReasoning("High-risk patterns detected. Escalating to Multi-Agent AI.");
//        }
//
//        // Populate data for React "Evidence Cards"
//        fc.setTransactionSummary(transactionToMap(event));
//        fc.setDetectionSignals(result.getSignals());
//        fc.setInvestigationLayers(List.of("RULE_BASED"));
//
//        // Save and immediately push to React Dashboard
//        FraudCase saved = fraudCaseRepository.saveAndFlush(fc);



        FraudCase fraudCase = new FraudCase();

        fraudCase.setCaseId(event.getCaseId());
        fraudCase.setStatus(status);
        fraudCase.setUserId(event.getUserId());
        fraudCase.setTriggerTransactionId(event.getTransactionId());
        fraudCase.setTriggeredBy("RULE_ENGINE");

        Instant now = Instant.now();
        fraudCase.setCreatedAt(now);
        fraudCase.setUpdatedAt(now);


        try {
            // Map Transaction Summary
            Map<String, Object> summary = new HashMap<>();
            summary.put("amount", event.getAmount());
            summary.put("currency", event.getCurrency());
            summary.put("type", event.getTransactionType());
            summary.put("paymentMethod", event.getPaymentMethod());
            fraudCase.setTransactionSummary(summary);

            // Map Identity Flags
            if (event.getUserProfile() != null) {
                fraudCase.setIdentityFlags(objectMapper.convertValue(event.getUserProfile(), Map.class));
            }

            // Map Behavioral/Network Flags from the event profiles
            if (event.getIpProfile() != null) {
                fraudCase.setNetworkFlags(objectMapper.convertValue(event.getIpProfile(), Map.class));
            }

            if (event.getFlags() != null) {
                fraudCase.setBehavioralFlags(objectMapper.convertValue(event.getFlags(), Map.class));
            }

        } catch (Exception e) {
            log.warn("Could not fully map JSON flags for case {}, saving partial: {}", event.getCaseId(), e.getMessage());
        }

        // 5. AI Investigation Metadata
        fraudCase.setAiReasoning("Rule Engine identified high-risk patterns. Escalating to AI for multi-layer analysis.");
        fraudCase.setInvestigationLayers(List.of("RULE_BASED"));

        // 6. Save to DB
        try {
            var saved = fraudCaseRepository.saveAndFlush(fraudCase);
            if (status.equals(CaseStatus.UNDER_INVESTIGATION)) {
                alertService.pushToDashboard(saved);
            }
            log.info("SUCCESS: Initialized FraudCase {} for user {}", event.getCaseId(), event.getUserId());
        } catch (Exception e) {
            log.error("CRITICAL: Failed to save FraudCase to DB: {}", e.getMessage());
        }

    }

    // ---------------------------
    // Push gray-area transactions to AI
    // ---------------------------
    private void queueForAIInvestigation(List<TransactionEvent> events, String caseId) {
        for (TransactionEvent event : events) {
            try {
                Map<String, String> payload = new HashMap<>();
                payload.put("case_id", caseId);
                payload.put("user_id", event.getUserId());
                payload.put("event_data", objectMapper.writeValueAsString(event));

                redisTemplate.opsForStream().add(
                        StreamRecords.newRecord().in(AI_QUEUE).ofMap(payload)
                );
            } catch (Exception e) {
                log.error("Failed to enqueue AI investigation for user {}: {}", event.getUserId(), e.getMessage());
            }
        }

        log.info("Queued {} transactions for AI investigation", events.size());
    }

    // ---------------------------
    // Helpers
    // ---------------------------
    private TransactionEvent parseEvent(MapRecord<String, Object, Object> record) throws Exception {
        Object raw = record.getValue().get("event_data");
        if (raw == null) {
            throw new IllegalArgumentException("Missing event_data field in record: " + record.getId());
        }

        String json = raw.toString(); // safely convert Object → String
        return objectMapper.readValue(json, TransactionEvent.class);
    }


    private Map<String, Object> transactionToMap(TransactionEvent event) {
        Map<String, Object> map = new HashMap<>();
        map.put("transactionId", event.getTransactionId());
        map.put("amount", event.getAmount());
        map.put("transactionType", event.getTransactionType());
        map.put("currency", event.getCurrency());
        map.put("paymentMethod", event.getPaymentMethod());
        map.put("paymentProvider", event.getPaymentProvider());
        map.put("ipAddress", event.getIpAddress());
        map.put("deviceId", event.getDeviceId());
        map.put("countryCode", event.getCountryCode());
        return map;
    }

    private boolean hasRapidDepositWithdrawal(TransactionEvent event) {
        // TODO: implement actual velocity check
        return false;
    }
}
