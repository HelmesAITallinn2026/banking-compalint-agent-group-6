package com.bcag6.mapper;

import com.bcag6.dto.AttachmentDto;
import com.bcag6.entity.ComplaintAttachment;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface AttachmentMapper {

    @Mapping(target = "complaintId", source = "complaint.id")
    AttachmentDto toDto(ComplaintAttachment attachment);

    List<AttachmentDto> toDtoList(List<ComplaintAttachment> attachments);
}
