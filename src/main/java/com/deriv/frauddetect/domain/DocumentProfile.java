package com.deriv.frauddetect.domain;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class DocumentProfile {
    private String verificationStatus; // PASSED, FAILED
    private BigDecimal confidenceScore;
    private BigDecimal faceMatchScore;

    private boolean forged;
    private boolean aiGenerated;
    private boolean expired;

    private BigDecimal documentQualityScore;
}
