package application;

import protocol.BankSession;
import protocol.DataMessage;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;


public final class BankTransactionService {
    private final BankService bankService;
    private final Map<String, BankSession> sessionsById = new HashMap<>();

    public BankTransactionService(BankService bankService) {
        this.bankService = bankService;
    }

    public DataMessage process(DataMessage request) {
        String command = request.getPayload().getCommand();

        if (command.equals("LOGOUT")) {
            sessionsById.remove(request.getSessionId());
            return responseFor(request, "LOGOUT_ACK", "");
        }

        BankSession session = sessionsById.computeIfAbsent(
            request.getSessionId(),
            ignoredSessionId -> new BankSession()
        );

        return switch (session.getPhase()) {
            case WAITING_START -> processStartTransaction(request, session);
            case WAITING_CARD -> processCard(request, session);
            case WAITING_PIN -> processPin(request, session);
            case WAITING_OPTION -> processOption(request, session);
            case WAITING_AMOUNT -> processAmount(request, session);
            case COMPLETED -> responseFor(request, "PROTOCOL_ERROR", "La operación ya terminó.");
        };
    }

    private DataMessage processStartTransaction(DataMessage request, BankSession session) {
        if (!request.getPayload().getCommand().equals("START_TRANSACTION")) {
            return protocolError(request, "START_TRANSACTION");
        }
        session.startTransaction();
        return responseFor(request, "TRANSACTION_READY", "");
    }

    private DataMessage processCard(DataMessage request, BankSession session) {
        if (!request.getPayload().getCommand().equals("CARD")) {
            return protocolError(request, "CARD");
        }
        BankAccount account = bankService.findAccount(request.getPayload().getPayload());
        if (account == null) {
            sessionsById.remove(request.getSessionId());
            return responseFor(request, "CARD_INVALID", "");
        }
        session.selectAccount(account);
        return responseFor(request, "CARD_ACCEPTED", "");
    }

    private DataMessage processPin(DataMessage request, BankSession session) {
        if (!request.getPayload().getCommand().equals("PIN")) {
            return protocolError(request, "PIN");
        }
        if (!bankService.validatePin(session.getSelectedAccount(), request.getPayload().getPayload())) {
            sessionsById.remove(request.getSessionId());
            return responseFor(request, "PIN_INCORRECT", "");
        }
        session.acceptPin();
        return responseFor(request, "PIN_ACCEPTED", "");
    }

    private DataMessage processOption(DataMessage request, BankSession session) {
        if (!request.getPayload().getCommand().equals("OPTION")) {
            return protocolError(request, "OPTION");
        }
        String option = request.getPayload().getPayload();
        if (option.equals("1")) {
            session.completeOperation();
            return responseFor(request, "BALANCE", Integer.toString(bankService.getBalance(session.getSelectedAccount())));
        }
        if (option.equals("2")) {
            session.selectWithdrawal();
            return responseFor(request, "REQUEST_AMOUNT", "");
        }
        return protocolError(request, "OPTION con valor 1 o 2");
    }

    private DataMessage processAmount(DataMessage request, BankSession session) {
        if (!request.getPayload().getCommand().equals("AMOUNT")) {
            return protocolError(request, "AMOUNT");
        }
        int withdrawalAmount;
        try {
            withdrawalAmount = Integer.parseInt(request.getPayload().getPayload());
        } catch (NumberFormatException exception) {
            return protocolError(request, "AMOUNT numérico");
        }
        if (withdrawalAmount <= 0) {
            return protocolError(request, "AMOUNT positivo");
        }
        if (!bankService.hasSufficientFunds(session.getSelectedAccount(), withdrawalAmount)) {
            return responseFor(request, "INSUFFICIENT_FUNDS", Integer.toString(bankService.getBalance(session.getSelectedAccount())));
        }
        bankService.withdraw(session.getSelectedAccount(), withdrawalAmount);
        session.completeOperation();
        return responseFor(request, "WITHDRAWAL_SUCCESSFUL", Integer.toString(bankService.getBalance(session.getSelectedAccount())));
    }

    private DataMessage protocolError(DataMessage request, String expectedValue) {
        return responseFor(request, "PROTOCOL_ERROR", "Se esperaba " + expectedValue + ".");
    }

    private DataMessage responseFor(DataMessage request, String command, String payload) {
        return new DataMessage(
            UUID.randomUUID().toString(),
            request.getSessionId(),
            request.getDestination(),
            request.getOrigin(),
            request.getNoise(),
            new DataMessage.BankPayload(command, payload)
        );
    }
}
