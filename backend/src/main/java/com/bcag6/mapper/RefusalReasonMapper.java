package com.bcag6.mapper;

import com.bcag6.dto.RefusalReasonDto;
import com.bcag6.entity.RefusalReason;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface RefusalReasonMapper {

    RefusalReasonDto toDto(RefusalReason reason);

    List<RefusalReasonDto> toDtoList(List<RefusalReason> reasons);
}
