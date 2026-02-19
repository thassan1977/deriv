package com.deriv.frauddetect.controller;

import com.deriv.frauddetect.entity.FraudCase;
import com.deriv.frauddetect.service.FraudCaseService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/dashboard")
@CrossOrigin(origins = "*") // For hackathon ease
@RequiredArgsConstructor
public class FraudDashboardController {
    private final FraudCaseService service;

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Long>> getStats() {
        return ResponseEntity.ok(service.getStats());
    }

    @GetMapping("/queue")
    public ResponseEntity<List<FraudCase>> getQueue() {
        return ResponseEntity.ok(service.getManualReviewQueue());
    }

    @GetMapping("/cases/{caseId}")
    public ResponseEntity<FraudCase> getCase(@PathVariable String caseId) {
        return service.getCaseById(caseId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/cases/{caseId}/resolve")
    public ResponseEntity<FraudCase> resolve(
            @PathVariable String caseId,
            @RequestBody Map<String, String> request) {
        return ResponseEntity.ok(service.resolveCase(
                caseId,
                request.get("decision"),
                request.get("notes")
        ));
    }
}