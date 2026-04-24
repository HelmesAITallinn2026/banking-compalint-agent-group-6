package com.bcag6.controller;

import com.bcag6.dto.ComplaintStatusDto;
import com.bcag6.entity.ComplaintStatus;
import com.bcag6.repository.ComplaintStatusRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/complaint-statuses")
@RequiredArgsConstructor
@Tag(name = "Complaint Statuses", description = "Lookup list of complaint statuses")
public class ComplaintStatusController {

    private final ComplaintStatusRepository complaintStatusRepository;

    @GetMapping
    @Operation(summary = "Get all complaint statuses")
    public ResponseEntity<List<ComplaintStatusDto>> getAll() {
        List<ComplaintStatusDto> result = complaintStatusRepository.findAll().stream()
            .map(s -> {
                ComplaintStatusDto dto = new ComplaintStatusDto();
                dto.setId(s.getId());
                dto.setName(s.getName());
                dto.setComment(s.getComment());
                return dto;
            })
            .toList();
        return ResponseEntity.ok(result);
    }
}
