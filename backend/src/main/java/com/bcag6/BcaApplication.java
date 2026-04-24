package com.bcag6;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class BcaApplication {

    public static void main(String[] args) {
        SpringApplication.run(BcaApplication.class, args);
    }
}
