package com.bcag6.controller;

import com.bcag6.dto.AgentDetailDto;
import com.bcag6.dto.AgentLogDto;
import com.bcag6.dto.AgentUpdateRequest;
import com.bcag6.dto.AttachmentDto;
import com.bcag6.dto.ComplaintDto;
import com.bcag6.dto.GenerateDraftRequest;
import com.bcag6.entity.ComplaintAttachment;
import com.bcag6.service.AgentClient;
import com.bcag6.service.AgentLogService;
import com.bcag6.service.AttachmentService;
import com.bcag6.service.ComplaintService;
import com.bcag6.service.FileStorageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/complaints")
@RequiredArgsConstructor
@Tag(name = "Complaints", description = "Complaint lifecycle management")
public class ComplaintController {

    private final ComplaintService complaintService;
    private final FileStorageService fileStorageService;
    private final AttachmentService attachmentService;
    private final AgentLogService agentLogService;
    private final AgentClient agentClient;

    @GetMapping
    @Operation(summary = "Get all complaints with optional status filter")
    public ResponseEntity<List<ComplaintDto>> getAll(
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(complaintService.getComplaints(status));
    }

    @GetMapping("/by-status/{statusId}")
    @Operation(summary = "Get complaints by status ID")
    public ResponseEntity<List<ComplaintDto>> getByStatusId(@PathVariable Integer statusId) {
        return ResponseEntity.ok(complaintService.getComplaintsByStatusId(statusId));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get complaint by ID")
    public ResponseEntity<ComplaintDto> getById(@PathVariable Long id) {
        return ResponseEntity.ok(complaintService.getComplaintById(id));
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "Create a new complaint")
    public ResponseEntity<ComplaintDto> create(
            @RequestParam Long customerId,
            @RequestParam String subject,
            @RequestParam String text,
            @RequestPart(name = "files", required = false) List<MultipartFile> files
    ) throws IOException {
        List<ComplaintAttachment> attachments = new ArrayList<>();
        if (files != null) {
            for (MultipartFile file : files) {
                if (file != null && !file.isEmpty()) {
                    attachments.add(fileStorageService.store(file));
                }
            }
        }
        ComplaintDto created = complaintService.createComplaint(customerId, subject, text, attachments);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PostMapping("/{id}/approve")
    @Operation(summary = "Approve draft and send email — sets status to Completed")
    public ResponseEntity<ComplaintDto> approve(@PathVariable Long id) {
        return ResponseEntity.ok(complaintService.approveComplaint(id));
    }

    @PatchMapping("/{id}/status")
    @Operation(summary = "Change complaint status and update updated_dttm")
    public ResponseEntity<ComplaintDto> changeStatus(
            @PathVariable Long id,
            @RequestParam Integer statusId) {
        return ResponseEntity.ok(complaintService.changeStatus(id, statusId));
    }

    @PatchMapping("/{id}/draft-email")
    @Operation(summary = "Update draft email subject and body")
    public ResponseEntity<ComplaintDto> updateDraftEmail(
            @PathVariable Long id,
            @RequestParam String subject,
            @RequestParam String body) {
        return ResponseEntity.ok(complaintService.updateDraftEmail(id, subject, body));
    }

    @GetMapping("/{id}/attachments")
    @Operation(summary = "List attachments for a complaint")
    public ResponseEntity<List<AttachmentDto>> getAttachments(@PathVariable Long id) {
        return ResponseEntity.ok(attachmentService.getAttachmentsByComplaintId(id));
    }

    @GetMapping("/{complaintId}/attachments/{attachmentId}/file")
    @Operation(summary = "Download or view an attachment file by complaint ID and attachment ID")
    public ResponseEntity<Resource> downloadAttachment(
            @PathVariable Long complaintId,
            @PathVariable Long attachmentId) throws IOException {
        ComplaintAttachment meta = attachmentService.getAttachmentEntityForComplaint(complaintId, attachmentId);
        Resource resource = attachmentService.streamFile(attachmentId);

        String mimeType = meta.getMimeType() != null ? meta.getMimeType() : MediaType.APPLICATION_OCTET_STREAM_VALUE;
        boolean viewable = mimeType.startsWith("image/") || mimeType.equals(MediaType.APPLICATION_PDF_VALUE);
        ContentDisposition disposition = viewable
            ? ContentDisposition.inline().filename(meta.getFileName()).build()
            : ContentDisposition.attachment().filename(meta.getFileName()).build();

        return ResponseEntity.ok()
            .contentType(MediaType.parseMediaType(mimeType))
            .header(HttpHeaders.CONTENT_DISPOSITION, disposition.toString())
            .body(resource);
    }

    // ── Agent integration endpoints ─────────────────────────────────────

    @PatchMapping("/{id}/agent-update")
    @Operation(summary = "Agent pushes processing results (status, extracted data, category, recommendation, draft)")
    public ResponseEntity<ComplaintDto> agentUpdate(
            @PathVariable Long id,
            @RequestBody AgentUpdateRequest request) {
        return ResponseEntity.ok(complaintService.agentUpdate(id, request));
    }

    @GetMapping("/{id}/agent-detail")
    @Operation(summary = "Get enriched complaint detail for agent processing")
    public ResponseEntity<AgentDetailDto> getAgentDetail(@PathVariable Long id) {
        return ResponseEntity.ok(complaintService.getAgentDetail(id));
    }

    @PostMapping("/{id}/generate-draft")
    @Operation(summary = "Operator triggers draft generation via agent")
    public ResponseEntity<Void> generateDraft(
            @PathVariable Long id,
            @RequestBody GenerateDraftRequest request) {
        complaintService.getComplaintById(id);
        agentClient.triggerDraftGeneration(id, request);
        return ResponseEntity.accepted().build();
    }

    @PostMapping("/{id}/agent-logs")
    @Operation(summary = "Agent pushes a processing log entry")
    public ResponseEntity<AgentLogDto> createAgentLog(
            @PathVariable Long id,
            @RequestBody AgentLogDto logDto) {
        return ResponseEntity.status(HttpStatus.CREATED).body(agentLogService.createLog(id, logDto));
    }

    @GetMapping("/{id}/agent-logs")
    @Operation(summary = "Get agent processing logs for a complaint")
    public ResponseEntity<List<AgentLogDto>> getAgentLogs(@PathVariable Long id) {
        return ResponseEntity.ok(agentLogService.getLogsByComplaintId(id));
    }
}
