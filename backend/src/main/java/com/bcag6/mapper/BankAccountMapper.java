package com.bcag6.mapper;

import com.bcag6.dto.BankAccountDto;
import com.bcag6.entity.BankAccount;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

import java.util.List;

@Mapper(componentModel = "spring")
public interface BankAccountMapper {

    @Mapping(target = "customerId", source = "customer.id")
    @Mapping(target = "accountType", expression = "java(account.getAccountType() != null ? account.getAccountType().name() : null)")
    BankAccountDto toDto(BankAccount account);

    List<BankAccountDto> toDtoList(List<BankAccount> accounts);
}
