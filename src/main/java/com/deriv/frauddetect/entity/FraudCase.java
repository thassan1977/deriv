package com.deriv.frauddetect.entity;

import com.deriv.frauddetect.enums.CaseStatus;
import com.vladmihalcea.hibernate.type.json.JsonType;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.Type;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@Entity
@Table(name = "fraud_cases")
@Data
public class FraudCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "case_id", unique = true)
    private String caseId;

    @Column(name = "user_id")
    private String userId;

    @Column(name = "created_at")
    private Instant createdAt;
    @Column(name = "updated_at")
    private Instant updatedAt;

    @Enumerated(EnumType.STRING)
    private CaseStatus status;
    @Column(name = "confidence_score")
    private BigDecimal confidenceScore;
    @Column(name = "fraud_probability")
    private BigDecimal fraudProbability;

    @Column(name = "triggered_by")
    private String triggeredBy; // RULE_ENGINE, ML_MODEL, PATTERN_MATCH, MANUAL_FLAG

    @Column(name = "trigger_transaction_id")
    private String triggerTransactionId;

    @Type(JsonType.class)
    @Column(name = "detection_signals",columnDefinition = "jsonb")
    private Map<String, Object> detectionSignals;

    @Type(JsonType.class)
    @Column(name = "transaction_summary",columnDefinition = "jsonb")
    private Map<String, Object> transactionSummary;

    @Type(JsonType.class)
    @Column(name = "identity_flags",columnDefinition = "jsonb")
    private Map<String, Object> identityFlags;

    @Type(JsonType.class)
    @Column(name = "behavioral_flags",columnDefinition = "jsonb")
    private Map<String, Object> behavioralFlags;

    @Type(JsonType.class)
    @Column(name = "network_flags", columnDefinition = "jsonb")
    private Map<String, Object> networkFlags;

    @Column(name = "processing_time_ms")
    private Integer processingTimeMs;

    // === EXTENDED FIELDS ===

    // Human in the loop
    @Column(name = "assigned_to")
    private String assignedTo;

    @Column(name = "human_decision")
    private String humanDecision; // APPROVED, BLOCKED, ESCALATED, RESOLVED

    @Column(name = "resolved_at")
    private Instant resolvedAt;

    @Column(name = "resolution_notes")
    private String resolutionNotes;

    // AI investigation
    @Type(JsonType.class)
    @Column(name = "ai_signals", columnDefinition = "jsonb")
    private Map<String, Object> aiSignals;

    @Column(name = "ai_reasoning")
    private String aiReasoning;

    @Column(name = "ai_recommendations")
    private String aiRecommendations;

    // Related network/fraud ring analysis
    @Type(JsonType.class)
    @Column(name = "related_accounts", columnDefinition = "jsonb")
    private List<Long> relatedAccounts; // user IDs


    @Column(name = "fraud_ring_id")
    private String fraudRingId;

    // Layers of processing
    @Type(JsonType.class)
    @Column(name = "investigation_layers", columnDefinition = "jsonb")
    private List<String> investigationLayers; // ['RULE_BASED', 'ML_MODELS', 'LLM_REASONING']
}
