package com.bcag6.service;

import com.bcag6.dto.RefusalReasonDto;
import com.bcag6.mapper.RefusalReasonMapper;
import com.bcag6.repository.RefusalReasonRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class RefusalReasonService {

    private final RefusalReasonRepository refusalReasonRepository;
    private final RefusalReasonMapper refusalReasonMapper;

    @Transactional(readOnly = true)
    public List<RefusalReasonDto> getAllRefusalReasons() {
        return refusalReasonMapper.toDtoList(refusalReasonRepository.findAll());
    }
}
