package com.deriv.frauddetect.controller;

import com.deriv.frauddetect.entity.FraudCase;
import com.deriv.frauddetect.enums.CaseStatus;
import com.deriv.frauddetect.service.FraudCaseService;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/fraud-cases")
@RequiredArgsConstructor
@Slf4j
public class FraudCaseController {

    private final FraudCaseService fraudCaseService;

    /**
     * Endpoint for AI investigator to update case results
     *
     * Sample payload:
     * {
     *   "caseId": "CASE-1679999999999",
     *   "decision": "AUTO_BLOCKED",
     *   "confidenceScore": 0.96,
     *   "aiReasoning": "User deposit much higher than declared income...",
     *   "aiRecommendations": "Block account and notify AML team",
     *   "detectionSignals": {
     *       "income_mismatch": true,
     *       "vpn_usage": true
     *   }
     * }
     */
    @PostMapping("/ai-update")
    public ResponseEntity<FraudCase> updateCaseFromAI(@RequestBody Map<String, Object> payload) {
        try {
            log.info("Received AI update for case: {}", payload.get("caseId"));
            FraudCase updated = fraudCaseService.processAiUpdate(payload);
            return ResponseEntity.ok(updated);
        } catch (EntityNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            log.error("Failed to update fraud case from AI", e);
            return ResponseEntity.badRequest().build();
        }
    }
//
//    @PostMapping("/ai-update")
//    public ResponseEntity<FraudCase> updateCaseFromAI(@RequestBody Map<String, Object> payload) {
//        try {
//            String caseId = (String) payload.get("caseId");
//            String decision = (String) payload.get("decision");
//            Double confidence = payload.get("confidenceScore") != null
//                    ? ((Number) payload.get("confidenceScore")).doubleValue() : null;
//            String aiReasoning = (String) payload.get("aiReasoning");
//            String aiRecommendations = (String) payload.get("aiRecommendations");
//            @SuppressWarnings("unchecked")
//            Map<String, Object> detectionSignals = (Map<String, Object>) payload.get("detectionSignals");
//
//            // Fetch and update the fraud case
//            FraudCase updated = fraudCaseService.addAiInvestigation(
//                    caseId,
//                    aiReasoning,
//                    aiRecommendations,
//                    detectionSignals
//            );
//
//            // Update status based on AI decision
//            if (CaseStatus.AUTO_BLOCKED.name().equalsIgnoreCase(decision) ||
//                    CaseStatus.AUTO_APPROVED.name().equalsIgnoreCase(decision)) {
//                updated.setStatus(CaseStatus.fromString(decision));
//            } else {
//                updated.setStatus(CaseStatus.UNDER_INVESTIGATION); // Needs human review
//            }
//
//            if (confidence != null) {
//                updated.setConfidenceScore(BigDecimal.valueOf(confidence));
//            }
//
//            return ResponseEntity.ok(fraudCaseService.updateCase(updated));
//        } catch (Exception e) {
//            log.error("Failed to update fraud case from AI", e);
//            return ResponseEntity.badRequest().build();
//        }
//    }

    /**
     * Optional: Get a case by caseId
     */
    @GetMapping("/{caseId}")
    public ResponseEntity<FraudCase> getCase(@PathVariable String caseId) {
        return fraudCaseService.getCaseById(caseId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
