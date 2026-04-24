package com.bcag6.repository;

import com.bcag6.entity.ComplaintStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ComplaintStatusRepository extends JpaRepository<ComplaintStatus, Integer> {

    Optional<ComplaintStatus> findByName(String name);
}
