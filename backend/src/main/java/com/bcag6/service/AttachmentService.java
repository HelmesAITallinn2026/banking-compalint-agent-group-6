package com.bcag6.service;

import com.bcag6.dto.AttachmentDto;
import com.bcag6.entity.ComplaintAttachment;
import com.bcag6.exception.ResourceNotFoundException;
import com.bcag6.mapper.AttachmentMapper;
import com.bcag6.repository.ComplaintAttachmentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AttachmentService {

    private final ComplaintAttachmentRepository attachmentRepository;
    private final AttachmentMapper attachmentMapper;

    @Transactional(readOnly = true)
    public List<AttachmentDto> getAttachmentsByComplaintId(Long complaintId) {
        return attachmentMapper.toDtoList(
            attachmentRepository.findByComplaint_Id(complaintId)
        );
    }

    @Transactional(readOnly = true)
    public ComplaintAttachment getAttachmentEntity(Long attachmentId) {
        return attachmentRepository.findById(attachmentId)
            .orElseThrow(() -> new ResourceNotFoundException("Attachment not found with id: " + attachmentId));
    }

    public Resource streamFile(Long attachmentId) throws IOException {
        ComplaintAttachment attachment = getAttachmentEntity(attachmentId);

        Path filePath = Paths.get(attachment.getFilePath()).normalize();

        // Security: resolve to absolute path and verify the file exists
        if (!Files.exists(filePath) || !Files.isRegularFile(filePath)) {
            throw new ResourceNotFoundException("File not found on disk for attachment id: " + attachmentId);
        }

        return new InputStreamResource(new FileInputStream(filePath.toFile()));
    }
}
