package com.deriv.frauddetect.enums;

public enum CaseStatus {
    AUTO_APPROVED,
    AUTO_BLOCKED,
    UNDER_INVESTIGATION,
    ESCALATED,
    RESOLVED;

    public static CaseStatus fromString(String status) {
        if (status == null) {
            throw new IllegalArgumentException("Status string cannot be null");
        }
        for (CaseStatus cs : CaseStatus.values()) {
            if (cs.name().equalsIgnoreCase(status.trim())) {
                return cs;
            }
        }
        throw new IllegalArgumentException("No enum constant for status: " + status);
    }
}
