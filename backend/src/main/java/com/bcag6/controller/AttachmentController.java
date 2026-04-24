package com.bcag6.controller;

import com.bcag6.entity.ComplaintAttachment;
import com.bcag6.service.AttachmentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;

@RestController
@RequiredArgsConstructor
@Tag(name = "Attachments", description = "Complaint file attachments")
public class AttachmentController {

    private final AttachmentService attachmentService;

    @GetMapping("/api/attachments/{id}/file")
    @Operation(summary = "Download or view a single attachment file")
    public ResponseEntity<Resource> downloadFile(@PathVariable Long id) throws IOException {
        ComplaintAttachment meta = attachmentService.getAttachmentEntity(id);
        Resource resource = attachmentService.streamFile(id);

        String mimeType = meta.getMimeType() != null ? meta.getMimeType() : MediaType.APPLICATION_OCTET_STREAM_VALUE;

        // Inline disposition for images and PDFs so browser renders them; force download otherwise
        boolean viewable = mimeType.startsWith("image/") || mimeType.equals(MediaType.APPLICATION_PDF_VALUE);
        ContentDisposition disposition = viewable
            ? ContentDisposition.inline().filename(meta.getFileName()).build()
            : ContentDisposition.attachment().filename(meta.getFileName()).build();

        return ResponseEntity.ok()
            .contentType(MediaType.parseMediaType(mimeType))
            .header(HttpHeaders.CONTENT_DISPOSITION, disposition.toString())
            .body(resource);
    }
}
