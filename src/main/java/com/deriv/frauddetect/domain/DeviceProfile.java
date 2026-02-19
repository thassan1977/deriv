package com.deriv.frauddetect.domain;

import lombok.Data;

@Data
public class DeviceProfile {
    private String deviceId;
    private String deviceType;
    private String os;
    private String browser;
    private String browserVersion;
    private String userAgent;
    private String screenResolution;
    private String timezone;
    private String language;

    private boolean emulator;
    private boolean vpn;
    private boolean proxy;
    private boolean tor;

    private int totalUsersCount;
    private int flaggedUsersCount;
}
