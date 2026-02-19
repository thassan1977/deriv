package com.deriv.frauddetect;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class DerivFraudApplication {

    public static void main(String[] args) {
        SpringApplication.run(DerivFraudApplication.class, args);
    }

}
