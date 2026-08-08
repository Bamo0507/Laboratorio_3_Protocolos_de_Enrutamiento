package application;


public final class BankAccount {
    private final String cardNumber;
    private final String ownerName;
    private final String pin;
    private int balance;

    public BankAccount(
        String cardNumber,
        String ownerName,
        String pin,
        int balance
    ) {
        this.cardNumber = cardNumber;
        this.ownerName = ownerName;
        this.pin = pin;
        this.balance = balance;
    }

    public String getCardNumber() {
        return cardNumber;
    }

    public String getOwnerName() {
        return ownerName;
    }

    public boolean isPinCorrect(String providedPin) {
        return pin.equals(providedPin);
    }

    public int getBalance() {
        return balance;
    }

    public boolean hasSufficientFunds(int withdrawalAmount) {
        return withdrawalAmount <= balance;
    }

    public void withdraw(int withdrawalAmount) {
        balance = balance - withdrawalAmount;
    }
}
