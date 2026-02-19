package com.deriv.frauddetect.domain;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserProfile {
    private String userId;
    private String email;
    private String fullName;
    private Instant dateOfBirth;
    private String nationality;

    private BigDecimal declaredMonthlyIncome;
    private String occupation;
    private String employmentStatus;
    private String sourceOfFunds;
    private String accountStatus;
    private String riskLevel;
    private String kycStatus;
    private Instant createdAt;
    private Instant accountCreatedAt;
    private BigDecimal totalDeposits;
    private BigDecimal totalWithdrawals;
    private Integer transactionCount;
    private Integer totalDevices;
}
