package com.bcag6.service;

import com.bcag6.entity.ComplaintAttachment;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Set;
import java.util.UUID;

@Service
@Slf4j
public class FileStorageService {

    private static final Set<String> ALLOWED_CONTENT_TYPES = Set.of(
        "image/jpeg", "image/png", "image/gif",
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    );

    @Value("${app.upload.dir:${user.home}/bca-uploads}")
    private String uploadDir;

    public ComplaintAttachment store(MultipartFile file) throws IOException {
        String contentType = file.getContentType();
        if (contentType != null && !ALLOWED_CONTENT_TYPES.contains(contentType)) {
            throw new IllegalArgumentException("File type not allowed: " + contentType);
        }

        Path uploadPath = Paths.get(uploadDir);
        Files.createDirectories(uploadPath);

        // Sanitise original filename — used only for metadata, not for storage path
        String originalFilename = StringUtils.hasText(file.getOriginalFilename())
            ? file.getOriginalFilename().replaceAll("[^a-zA-Z0-9._\\-]", "_")
            : "file";

        // Store file under a UUID-prefixed name to prevent collisions and path traversal
        String storedName = UUID.randomUUID() + "_" + originalFilename;
        Path storedPath = uploadPath.resolve(storedName).normalize();

        // Guard against path traversal after normalization
        if (!storedPath.startsWith(uploadPath.toAbsolutePath().normalize())) {
            throw new SecurityException("Path traversal attempt detected.");
        }

        Files.copy(file.getInputStream(), storedPath, StandardCopyOption.REPLACE_EXISTING);
        log.debug("Stored file: {} -> {}", originalFilename, storedPath);

        ComplaintAttachment attachment = new ComplaintAttachment();
        attachment.setFileName(originalFilename);
        attachment.setFilePath(storedPath.toString());
        attachment.setMimeType(contentType);
        attachment.setFileSize(file.getSize());
        return attachment;
    }
}
