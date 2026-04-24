package com.bcag6.service;

import com.bcag6.dto.BankAccountDto;
import com.bcag6.mapper.BankAccountMapper;
import com.bcag6.repository.BankAccountRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class BankAccountService {

    private final BankAccountRepository bankAccountRepository;
    private final BankAccountMapper bankAccountMapper;

    @Transactional(readOnly = true)
    public List<BankAccountDto> getAccountsByCustomerId(Long customerId) {
        return bankAccountMapper.toDtoList(
            bankAccountRepository.findByCustomer_Id(customerId)
        );
    }
}
