package com.bcag6.service;

import com.bcag6.dto.AgentDetailDto;
import com.bcag6.dto.AgentUpdateRequest;
import com.bcag6.dto.ComplaintDto;
import com.bcag6.entity.*;
import com.bcag6.event.AiProcessingPublisher;
import com.bcag6.exception.BusinessException;
import com.bcag6.exception.ResourceNotFoundException;
import com.bcag6.mapper.ComplaintMapper;
import com.bcag6.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Random;

@Service
@RequiredArgsConstructor
@Slf4j
public class ComplaintService {

    private static final String STATUS_SUBMITTED   = "Submitted";
    private static final String STATUS_DRAFT       = "Draft Created";
    private static final String STATUS_COMPLETED   = "Completed";

    private final ComplaintRepository complaintRepository;
    private final ComplaintStatusRepository complaintStatusRepository;
    private final RefusalReasonRepository refusalReasonRepository;
    private final CustomerRepository customerRepository;
    private final ComplaintStatusLogRepository statusLogRepository;
    private final ComplaintAttachmentRepository attachmentRepository;
    private final AuditLogRepository auditLogRepository;
    private final ComplaintMapper complaintMapper;
    private final EmailService emailService;
    private final AiProcessingPublisher aiProcessingPublisher;

    @Transactional(readOnly = true)
    public List<ComplaintDto> getComplaints(String statusName) {
        List<Complaint> complaints = statusName != null
            ? complaintRepository.findByStatusNameWithDetails(statusName)
            : complaintRepository.findAllWithDetails();
        return complaintMapper.toDtoList(complaints);
    }

    @Transactional(readOnly = true)
    public List<ComplaintDto> getComplaintsByStatusId(Integer statusId) {
        return complaintMapper.toDtoList(complaintRepository.findByStatusIdWithDetails(statusId));
    }

    @Transactional(readOnly = true)
    public ComplaintDto getComplaintById(Long id) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));
        return complaintMapper.toDto(complaint);
    }

    @Transactional
    public ComplaintDto createComplaint(Long customerId, String subject, String text,
                                        List<ComplaintAttachment> attachments) {
        Customer customer = customerRepository.findById(customerId)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found with id: " + customerId));

        ComplaintStatus submittedStatus = complaintStatusRepository.findByName(STATUS_SUBMITTED)
            .orElseThrow(() -> new IllegalStateException("Status '" + STATUS_SUBMITTED + "' not found in database."));

        // Backend randomly assigns refusal reason — frontend selection is informational only
        List<RefusalReason> reasons = refusalReasonRepository.findAll();
        RefusalReason refusalReason = reasons.isEmpty()
            ? null
            : reasons.get(new Random().nextInt(reasons.size()));

        Complaint complaint = new Complaint();
        complaint.setCustomer(customer);
        complaint.setStatus(submittedStatus);
        complaint.setSubject(subject);
        complaint.setText(text);
        complaint.setRefusalReason(refusalReason);
        Complaint saved = complaintRepository.save(complaint);

        writeStatusLog(saved, submittedStatus);
        writeAuditLog("COMPLAINT", saved.getId(), AuditAction.CREATE,
            "{\"customerId\":" + customerId + ",\"subject\":\"" + escapeJson(subject) + "\"}");

        // Persist attachments
        for (ComplaintAttachment a : attachments) {
            a.setComplaint(saved);
            attachmentRepository.save(a);
        }

        // Trigger AI processing (stub)
        aiProcessingPublisher.publish(saved.getId());

        return complaintMapper.toDto(
            complaintRepository.findByIdWithDetails(saved.getId())
                .orElseThrow(() -> new IllegalStateException("Complaint not found after creation."))
        );
    }

    @Transactional
    public ComplaintDto approveComplaint(Long id) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));

        if (!STATUS_DRAFT.equals(complaint.getStatus().getName())) {
            throw new BusinessException(
                "Complaint must be in '" + STATUS_DRAFT + "' status to approve. " +
                "Current status: " + complaint.getStatus().getName());
        }

        ComplaintStatus completedStatus = complaintStatusRepository.findByName(STATUS_COMPLETED)
            .orElseThrow(() -> new IllegalStateException("Status '" + STATUS_COMPLETED + "' not found in database."));

        complaint.setStatus(completedStatus);
        complaint.setResolvedDttm(OffsetDateTime.now());
        complaintRepository.save(complaint);

        writeStatusLog(complaint, completedStatus);
        writeAuditLog("COMPLAINT", id, AuditAction.UPDATE,
            "{\"action\":\"approve\",\"newStatus\":\"" + STATUS_COMPLETED + "\"}");

        // Send draft email to customer
        String customerEmail = complaint.getCustomer().getEmail();
        emailService.sendDraftEmail(customerEmail,
            complaint.getDraftEmailSubject(), complaint.getDraftEmailBody());

        return complaintMapper.toDto(
            complaintRepository.findByIdWithDetails(id)
                .orElseThrow(() -> new IllegalStateException("Complaint not found after update."))
        );
    }

    @Transactional
    public ComplaintDto updateDraftEmail(Long id, String subject, String body) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));

        complaint.setDraftEmailSubject(subject);
        complaint.setDraftEmailBody(body);
        complaintRepository.save(complaint);

        writeAuditLog("COMPLAINT", id, AuditAction.UPDATE,
            "{\"action\":\"updateDraftEmail\"}");

        return complaintMapper.toDto(
            complaintRepository.findByIdWithDetails(id)
                .orElseThrow(() -> new IllegalStateException("Complaint not found after update."))
        );
    }

    @Transactional
    public ComplaintDto changeStatus(Long id, Integer statusId) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));

        ComplaintStatus newStatus = complaintStatusRepository.findById(statusId)
            .orElseThrow(() -> new ResourceNotFoundException("Status not found with id: " + statusId));

        String oldStatusName = complaint.getStatus().getName();
        complaint.setStatus(newStatus);
        complaint.setUpdatedDttm(OffsetDateTime.now());
        complaintRepository.save(complaint);

        writeStatusLog(complaint, newStatus);
        writeAuditLog("COMPLAINT", id, AuditAction.UPDATE,
            "{\"action\":\"statusChange\",\"from\":\"" + escapeJson(oldStatusName) +
            "\",\"to\":\"" + escapeJson(newStatus.getName()) + "\"}");

        return complaintMapper.toDto(
            complaintRepository.findByIdWithDetails(id)
                .orElseThrow(() -> new IllegalStateException("Complaint not found after update."))
        );
    }

    @Transactional
    public ComplaintDto agentUpdate(Long id, AgentUpdateRequest req) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));

        if (req.getStatusId() != null) {
            ComplaintStatus newStatus = complaintStatusRepository.findById(req.getStatusId())
                .orElseThrow(() -> new ResourceNotFoundException("Status not found with id: " + req.getStatusId()));
            complaint.setStatus(newStatus);
            writeStatusLog(complaint, newStatus);
        }
        if (req.getExtractedData() != null) complaint.setExtractedData(req.getExtractedData());
        if (req.getCategory() != null) complaint.setCategory(req.getCategory());
        if (req.getRecommendation() != null) complaint.setRecommendation(req.getRecommendation());
        if (req.getRecommendationReasoning() != null) complaint.setRecommendationReasoning(req.getRecommendationReasoning());
        if (req.getDraftEmailSubject() != null) complaint.setDraftEmailSubject(req.getDraftEmailSubject());
        if (req.getDraftEmailBody() != null) complaint.setDraftEmailBody(req.getDraftEmailBody());

        complaintRepository.save(complaint);

        writeAuditLog("COMPLAINT", id, AuditAction.UPDATE,
            "{\"action\":\"agentUpdate\",\"statusId\":" + req.getStatusId() + "}");

        return complaintMapper.toDto(
            complaintRepository.findByIdWithDetails(id)
                .orElseThrow(() -> new IllegalStateException("Complaint not found after update."))
        );
    }

    @Transactional(readOnly = true)
    public AgentDetailDto getAgentDetail(Long id) {
        Complaint complaint = complaintRepository.findByIdWithDetails(id)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + id));

        AgentDetailDto dto = new AgentDetailDto();
        dto.setId(complaint.getId());
        dto.setFirstName(complaint.getCustomer().getFirstName());
        dto.setLastName(complaint.getCustomer().getLastName());
        dto.setSubject(complaint.getSubject());
        dto.setText(complaint.getText());
        dto.setRefusalReason(complaint.getRefusalReason() != null ? complaint.getRefusalReason().getName() : null);
        dto.setStatusId(complaint.getStatus().getId());
        dto.setStatus(complaint.getStatus().getName());
        dto.setExtractedData(complaint.getExtractedData());
        dto.setCategory(complaint.getCategory());
        dto.setRecommendation(complaint.getRecommendation());
        dto.setRecommendationReasoning(complaint.getRecommendationReasoning());
        dto.setDraftEmailBody(complaint.getDraftEmailBody());
        dto.setCreatedDttm(complaint.getCreatedDttm());
        dto.setUpdatedDttm(complaint.getUpdatedDttm());

        List<ComplaintAttachment> attachments = attachmentRepository.findByComplaint_Id(complaint.getId());
        dto.setAttachments(attachments.stream().map(a -> {
            AgentDetailDto.AgentAttachmentDto adto = new AgentDetailDto.AgentAttachmentDto();
            adto.setId(a.getId());
            adto.setFileName(a.getFileName());
            adto.setMimeType(a.getMimeType());
            adto.setFileSize(a.getFileSize());
            return adto;
        }).toList());

        return dto;
    }

    // ── Helpers ─────────────────────────────────────────────────────────────

    private void writeStatusLog(Complaint complaint, ComplaintStatus status) {
        ComplaintStatusLog log = new ComplaintStatusLog();
        log.setComplaint(complaint);
        log.setStatus(status);
        statusLogRepository.save(log);
    }

    private void writeAuditLog(String entityType, Long entityId, AuditAction action, String details) {
        AuditLog entry = new AuditLog();
        entry.setEntityType(entityType);
        entry.setEntityId(entityId);
        entry.setAction(action);
        entry.setPerformedBy("SYSTEM");
        entry.setDetails(details);
        auditLogRepository.save(entry);
    }

    private String escapeJson(String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
