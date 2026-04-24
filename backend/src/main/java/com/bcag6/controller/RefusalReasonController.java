package com.bcag6.controller;

import com.bcag6.dto.RefusalReasonDto;
import com.bcag6.service.RefusalReasonService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/refusal-reasons")
@RequiredArgsConstructor
@Tag(name = "Refusal Reasons", description = "Lookup values for refusal reasons")
public class RefusalReasonController {

    private final RefusalReasonService refusalReasonService;

    @GetMapping
    @Operation(summary = "Get all refusal reasons")
    public ResponseEntity<List<RefusalReasonDto>> getAll() {
        return ResponseEntity.ok(refusalReasonService.getAllRefusalReasons());
    }
}
