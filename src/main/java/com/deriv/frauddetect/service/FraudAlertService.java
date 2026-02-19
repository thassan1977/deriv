package com.deriv.frauddetect.service;

import com.deriv.frauddetect.entity.FraudCase;
import com.deriv.frauddetect.repository.FraudCaseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FraudAlertService {
    private final SimpMessagingTemplate messagingTemplate;
    private final FraudCaseRepository fraudCaseRepository;

    private final TrafficMonitor trafficMonitor;

    private long lastCheckTime = System.currentTimeMillis();

    public void pushToDashboard(FraudCase updatedCase) {
        messagingTemplate.convertAndSend("/topic/queue", updatedCase);
    }

    @Scheduled(fixedRate = 1000)
    public void broadcastStats() {
        // 1. Calculate TPS
        long currentTime = System.currentTimeMillis();
        long timeDelta = currentTime - lastCheckTime;
        long count = trafficMonitor.getAndReset();

        double tps = (count / (timeDelta / 1000.0));
        lastCheckTime = currentTime;

        List<Object[]> results = fraudCaseRepository.getStatusStatistics();
        Map<String, Long> counts = results.stream()
                .collect(Collectors.toMap(
                        res -> res[0].toString(),
                        res -> (Long) res[1]
                ));

        Map<String, Object> stats = new HashMap<>();
        stats.put("total_cases", counts.values().stream().mapToLong(Long::longValue).sum());
        stats.put("auto_approved", counts.getOrDefault("AUTO_APPROVED", 0L));
        stats.put("auto_blocked", counts.getOrDefault("AUTO_BLOCKED", 0L));
        stats.put("manual_cases", counts.getOrDefault("UNDER_INVESTIGATION", 0L));

        stats.put("tps", (int) tps);

        messagingTemplate.convertAndSend("/topic/stats", stats);
    }
}