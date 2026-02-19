package com.deriv.frauddetect.service;

import com.deriv.frauddetect.entity.FraudCase;
import com.deriv.frauddetect.enums.CaseStatus;
import com.deriv.frauddetect.repository.FraudCaseRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FraudCaseService {

    private final FraudCaseRepository fraudCaseRepository;

//    /**
//     * Create a new fraud case from a transaction or AI/rule engine detection
//     */
//    @Transactional
//    public FraudCase createCase(FraudCase fraudCase) {
//        if (fraudCase.getCaseId() == null || fraudCase.getCaseId().isBlank()) {
//            fraudCase.setCaseId("CASE-" + Instant.now().toEpochMilli());
//        }
//
//        fraudCase.setCreatedAt(Instant.now());
//        fraudCase.setUpdatedAt(Instant.now());
//
//        return fraudCaseRepository.save(fraudCase);
//    }

    /**
     * Update an existing fraud case
     */
    public FraudCase processAiUpdate(Map<String, Object> payload) {
        String caseId = (String) payload.get("caseId");

        FraudCase fraudCase = fraudCaseRepository.findByCaseId(caseId)
                .orElseThrow(() -> new EntityNotFoundException("FraudCase not found: " + caseId));

        fraudCase.setAiReasoning((String) payload.get("aiReasoning"));
        fraudCase.setAiRecommendations((String) payload.get("aiRecommendations"));

        if (payload.get("confidenceScore") != null) {
            double confidence = ((Number) payload.get("confidenceScore")).doubleValue();
            fraudCase.setConfidenceScore(BigDecimal.valueOf(confidence));
        }

        @SuppressWarnings("unchecked")
        List<String> incomingLayers = (List<String>) payload.get("investigation_layers");
        if (incomingLayers != null) {
            Set<String> layers = new LinkedHashSet<>(fraudCase.getInvestigationLayers());
            layers.addAll(incomingLayers);
            fraudCase.setInvestigationLayers(new ArrayList<>(layers));
        }

        String decision = (String) payload.get("decision");
        if (CaseStatus.AUTO_BLOCKED.name().equalsIgnoreCase(decision) ||
                CaseStatus.AUTO_APPROVED.name().equalsIgnoreCase(decision)) {
            fraudCase.setStatus(CaseStatus.fromString(decision));
        } else {
            fraudCase.setStatus(CaseStatus.UNDER_INVESTIGATION);
        }

        if (payload.get("detectionSignals") != null) {
            @SuppressWarnings("unchecked")
            Map<String, Object> signals = (Map<String, Object>) payload.get("detectionSignals");
            fraudCase.setDetectionSignals(signals);
        }

        if (payload.get("ai_signals") != null) {
            @SuppressWarnings("unchecked")
            Map<String, Object> signals = (Map<String, Object>) payload.get("ai_signals");
            fraudCase.setAiSignals(signals);
        }

        return updateCase(fraudCase);
    }
    @Transactional
    public FraudCase updateCase(FraudCase fraudCase) {
        fraudCase.setUpdatedAt(Instant.now());
        return fraudCaseRepository.save(fraudCase);
    }

    /**
     * Mark a case as resolved
     */
    @Transactional
    public FraudCase resolveCase(String caseId, String humanDecision, String resolutionNotes) {
        Optional<FraudCase> optional = fraudCaseRepository.findByCaseId(caseId);
        if (optional.isEmpty()) {
            throw new IllegalArgumentException("Fraud case not found: " + caseId);
        }

        FraudCase fc = optional.get();
        fc.setHumanDecision(humanDecision);
        fc.setResolvedAt(Instant.now());
        fc.setResolutionNotes(resolutionNotes);
        fc.setStatus(CaseStatus.RESOLVED);
        fc.setUpdatedAt(Instant.now());

        return fraudCaseRepository.save(fc);
    }

    /**
     * Fetch cases by user
     */
    public List<FraudCase> getCasesByUser(String userId) {
        return fraudCaseRepository.findByUserId(userId);
    }

    /**
     * Fetch open cases
     */
    public List<FraudCase> getOpenCases() {
        return fraudCaseRepository.findByStatusIn(List.of(
                "AUTO_BLOCKED", "UNDER_INVESTIGATION", "ESCALATED"
        ));
    }

    /**
     * Add AI investigation results or signals
     */
    @Transactional
    public FraudCase addAiInvestigation(String caseId,
                                        String aiReasoning,
                                        String aiRecommendations,
                                        Map<String, Object> detectionSignals) {
        FraudCase fc = fraudCaseRepository.findByCaseId(caseId)
                .orElseThrow(() -> new IllegalArgumentException("Case not found: " + caseId));

        fc.setAiReasoning(aiReasoning);
        fc.setAiRecommendations(aiRecommendations);
        fc.setDetectionSignals(detectionSignals);
        fc.setUpdatedAt(Instant.now());

        return fraudCaseRepository.save(fc);
    }

    /**
     * get case by ID
     */
    @Transactional
    public Optional<FraudCase> getCaseById(String caseId) {
        return fraudCaseRepository.findByCaseId(caseId);
    }

    public Map<String, Long> getStats() {
        return fraudCaseRepository.getStatusStatistics().stream()
                .collect(Collectors.toMap(
                        o -> o[0].toString(),
                        o -> (Long) o[1]
                ));
    }

    public List<FraudCase> getManualReviewQueue() {
        return fraudCaseRepository.findByStatusInOrderByCreatedAtDesc(
                List.of("UNDER_INVESTIGATION", "ESCALATED")
        );
    }

}