package com.bcag6.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;

@Entity
@Table(name = "complaint_attachment")
@Getter
@Setter
@NoArgsConstructor
public class ComplaintAttachment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "complaint_id", nullable = false)
    private Complaint complaint;

    @Column(name = "file_name", nullable = false, length = 255)
    private String fileName;

    @Column(name = "file_path", nullable = false)
    private String filePath;

    @Column(name = "mime_type", length = 255)
    private String mimeType;

    @Column(name = "file_size")
    private Long fileSize;

    @Column(name = "uploaded_dttm", nullable = false)
    private OffsetDateTime uploadedDttm;

    @PrePersist
    protected void onCreate() {
        if (uploadedDttm == null) {
            uploadedDttm = OffsetDateTime.now();
        }
    }
}
