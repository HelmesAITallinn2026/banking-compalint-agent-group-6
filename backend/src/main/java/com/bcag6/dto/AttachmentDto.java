package com.bcag6.dto;

import lombok.Data;

import java.time.OffsetDateTime;

@Data
public class AttachmentDto {
    private Long id;
    private Long complaintId;
    private String fileName;
    private String mimeType;
    private Long fileSize;
    private OffsetDateTime uploadedDttm;
}
