package com.deriv.frauddetect.service;

import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicLong;

@Component
public class TrafficMonitor {
    private final AtomicLong counter = new AtomicLong(0);

    public void increment(int count) {
        counter.addAndGet(count);
    }

    public long getAndReset() {
        return counter.getAndSet(0);
    }
}