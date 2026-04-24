package com.bcag6.controller;

import com.bcag6.dto.ComplaintDto;
import com.bcag6.entity.ComplaintAttachment;
import com.bcag6.service.ComplaintService;
import com.bcag6.service.FileStorageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
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

    @GetMapping
    @Operation(summary = "Get all complaints with optional status filter")
    public ResponseEntity<List<ComplaintDto>> getAll(
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(complaintService.getComplaints(status));
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
}
