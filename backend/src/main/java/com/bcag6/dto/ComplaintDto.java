package com.bcag6.dto;

import lombok.Data;

import java.time.OffsetDateTime;

@Data
public class ComplaintDto {
    private Long id;
    private Long customerId;
    private String customerName;
    private Integer statusId;
    private String status;
    private OffsetDateTime createdDttm;
    private OffsetDateTime updatedDttm;
    private OffsetDateTime resolvedDttm;
    private String subject;
    private String text;
    private String draftEmailSubject;
    private String draftEmailBody;
    private Integer refusalReasonId;
    private String refusalReason;
    private String extractedData;
    private String category;
    private String recommendation;
    private String recommendationReasoning;
}
