package com.bcag6.repository;

import com.bcag6.entity.ComplaintAttachment;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ComplaintAttachmentRepository extends JpaRepository<ComplaintAttachment, Long> {

    List<ComplaintAttachment> findByComplaint_Id(Long complaintId);
}
