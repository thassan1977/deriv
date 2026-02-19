package com.deriv.frauddetect.domain;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TransactionEvent {

    private String caseId;

    private String email;
    private String fullName;
    private Instant dateOfBirth;
    private String nationality;

    private String transactionId;
    private String userId;
    private Instant createdAt;

    private String transactionType; // DEPOSIT, WITHDRAWAL, TRADE
    private BigDecimal amount;
    private String currency;

    private String paymentMethod;
    private String paymentProvider;

    private String ipAddress;
    private String deviceId;
    private String countryCode;

    private UserProfile userProfile;
    private DeviceProfile deviceProfile;
    private IpProfile ipProfile;
    private DocumentProfile documentProfile;
    private TransactionFlags flags;
    private Instant timestamp;
}
