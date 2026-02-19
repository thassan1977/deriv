package com.deriv.frauddetect.domain;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class IpProfile {
    private String ipAddress;
    private String countryCode;
    private String countryName;
    private String city;
    private String region;
    private String latitude;
    private String longitude;
    private String isp;
    private String organization;
    private String asn;
    private boolean vpn;
    private boolean proxy;
    private boolean tor;
    private boolean datacenter;
    private boolean anonymous;
    private boolean sanctionedCountry;
    private boolean highRiskCountry;

    private BigDecimal riskScore;
    private BigDecimal totalUsers;
    private BigDecimal flaggedUsers;

}
