package com.bcag6.repository;

import com.bcag6.entity.Complaint;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface ComplaintRepository extends JpaRepository<Complaint, Long> {

    @Query("SELECT c FROM Complaint c JOIN FETCH c.customer JOIN FETCH c.status LEFT JOIN FETCH c.refusalReason ORDER BY c.createdDttm DESC")
    List<Complaint> findAllWithDetails();

    @Query("SELECT c FROM Complaint c JOIN FETCH c.customer JOIN FETCH c.status LEFT JOIN FETCH c.refusalReason WHERE c.status.name = :statusName ORDER BY c.createdDttm DESC")
    List<Complaint> findByStatusNameWithDetails(@Param("statusName") String statusName);

    @Query("SELECT c FROM Complaint c JOIN FETCH c.customer JOIN FETCH c.status LEFT JOIN FETCH c.refusalReason WHERE c.status.id = :statusId ORDER BY c.createdDttm DESC")
    List<Complaint> findByStatusIdWithDetails(@Param("statusId") Integer statusId);

    @Query("SELECT c FROM Complaint c JOIN FETCH c.customer JOIN FETCH c.status LEFT JOIN FETCH c.refusalReason WHERE c.id = :id")
    Optional<Complaint> findByIdWithDetails(@Param("id") Long id);
}
