package com.bcag6.mapper;

import com.bcag6.dto.CustomerDto;
import com.bcag6.entity.Customer;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface CustomerMapper {

    CustomerDto toDto(Customer customer);
}
