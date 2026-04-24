package com.bcag6.mapper;

import com.bcag6.dto.ComplaintDto;
import com.bcag6.entity.Complaint;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface ComplaintMapper {

    @Mapping(target = "customerId", source = "customer.id")
    @Mapping(target = "customerName",
        expression = "java(complaint.getCustomer().getFirstName() + \" \" + complaint.getCustomer().getLastName())")
    @Mapping(target = "statusId", source = "status.id")
    @Mapping(target = "status", source = "status.name")
    @Mapping(target = "refusalReasonId", source = "refusalReason.id")
    @Mapping(target = "refusalReason", source = "refusalReason.name")
    ComplaintDto toDto(Complaint complaint);

    List<ComplaintDto> toDtoList(List<Complaint> complaints);
}
