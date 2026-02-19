package com.deriv.frauddetect.domain;

import com.deriv.frauddetect.enums.CaseStatus;
import lombok.Data;

import java.util.HashMap;
import java.util.Map;

@Data
public class RuleResult {

    private CaseStatus decision; // AUTO_APPROVED, AUTO_BLOCKED, NEEDS_INVESTIGATION
    private double confidence;
    private double riskScore;

    private Map<String, Object> signals = new HashMap<>();

    public boolean isDefinitive() {
        return CaseStatus.AUTO_APPROVED.equals(decision) ||
                CaseStatus.AUTO_BLOCKED.equals(decision);
    }

    public void addSignal(String key, Object value) {
        signals.put(key, value);
    }
}
