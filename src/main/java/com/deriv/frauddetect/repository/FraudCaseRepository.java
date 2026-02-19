package com.deriv.frauddetect.repository;

import com.deriv.frauddetect.entity.FraudCase;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface FraudCaseRepository extends JpaRepository<FraudCase, Long> {

    // Find by unique case ID
    Optional<FraudCase> findByCaseId(String caseId);

    // Find all cases for a specific user
    List<FraudCase> findByUserId(String userId);

    // Find all open/active cases by status
    List<FraudCase> findByStatusIn(List<String> statuses);

    // Optional: find cases assigned to a specific investigator
    List<FraudCase> findByAssignedTo(String assignedTo);

    // Optional: find cases that need AI investigation
    List<FraudCase> findByStatusAndConfidenceScoreLessThan(String status, java.math.BigDecimal confidenceThreshold);

    List<FraudCase> findByStatusInOrderByCreatedAtDesc(List<String> statuses);

    @Query("SELECT fraud.status, COUNT(*) FROM FraudCase fraud GROUP BY status")
    List<Object[]> getStatusStatistics();
}