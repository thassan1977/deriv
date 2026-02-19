package com.deriv.frauddetect.domain;

import lombok.Data;

@Data
public class TransactionFlags {
    private boolean velocityFlag;
    private boolean amountAnomalyFlag;
    private boolean geographicAnomalyFlag;
}
