# Activity Diagram / Flowchart - Slot Booking System

> **Platform Independence**: Flowcharts show generic business processes applicable to any booking domain.

---

## 1. User Registration Flow

```mermaid
flowchart TD
    Start([Start]) --> Visit[Visit Registration Page]
    Visit --> Choice{Registration Method}
    
    Choice -->|Email| EnterEmail[Enter Email & Password]
    Choice -->|Phone| EnterPhone[Enter Phone Number]
    Choice -->|Social| SocialAuth[Click Social Login]
    
    EnterEmail --> ValidateEmail{Valid Email?}
    ValidateEmail -->|No| EmailError[Show Error] --> EnterEmail
    ValidateEmail -->|Yes| CheckDupe{Email Exists?}
    CheckDupe -->|Yes| DupeError[Show Duplicate Error] --> EnterEmail
    CheckDupe -->|No| CreateAccount[Create Account]
    
    EnterPhone --> SendOTP[Send OTP]
    SendOTP --> EnterOTP[Enter OTP]
    EnterOTP --> ValidateOTP{Valid OTP?}
    ValidateOTP -->|No| OTPError[Show OTP Error] --> EnterOTP
    ValidateOTP -->|Yes| CreateAccount
    
    SocialAuth --> OAuthFlow[OAuth Provider Flow]
    OAuthFlow --> GetProfile[Get Profile Data]
    GetProfile --> CreateAccount
    
    CreateAccount --> SendVerification[Send Verification Email]
    SendVerification --> WaitVerify[Wait for Verification]
    WaitVerify --> Verified{Email Verified?}
    Verified -->|No| Resend{Resend?}
    Resend -->|Yes| SendVerification
    Resend -->|No| Timeout[Registration Expires]
    Verified -->|Yes| ActivateAccount[Activate Account]
    ActivateAccount --> Success([Registration Complete])
    Timeout --> Fail([Registration Failed])
```

---

## 2. Complete Booking Flow

```mermaid
flowchart TD
    Start([Start]) --> Browse[Browse Resources]
    Browse --> Select[Select Resource]
    Select --> ViewDetails[View Resource Details]
    ViewDetails --> PickDate[Select Date]
    PickDate --> CheckAvail{Slots Available?}
    
    CheckAvail -->|No| AltDate{Try Another Date?}
    AltDate -->|Yes| PickDate
    AltDate -->|No| Exit1([Exit])
    
    CheckAvail -->|Yes| ShowSlots[Display Available Slots]
    ShowSlots --> SelectSlot[Select Slot/s]
    SelectSlot --> LoggedIn{User Logged In?}
    
    LoggedIn -->|No| PromptLogin[Prompt Login/Register]
    PromptLogin --> DoLogin[Login/Register]
    DoLogin --> SelectSlot
    
    LoggedIn -->|Yes| ShowSummary[Show Booking Summary]
    ShowSummary --> AddPromo{Apply Promo?}
    AddPromo -->|Yes| EnterPromo[Enter Promo Code]
    EnterPromo --> ValidPromo{Valid Code?}
    ValidPromo -->|No| PromoError[Show Error] --> AddPromo
    ValidPromo -->|Yes| ApplyDiscount[Apply Discount]
    ApplyDiscount --> ShowSummary
    AddPromo -->|No| ConfirmBook[Confirm Booking]
    
    ConfirmBook --> SlotStillAvail{Slot Still Available?}
    SlotStillAvail -->|No| Conflict[Show Conflict] --> ShowSlots
    SlotStillAvail -->|Yes| LockSlot[Lock Slot Temporarily]
    
    LockSlot --> PaymentPage[Go to Payment]
    PaymentPage --> SelectMethod[Select Payment Method]
    SelectMethod --> EnterPayment[Enter Payment Details]
    EnterPayment --> ProcessPay[Process Payment]
    
    ProcessPay --> PayStatus{Payment Success?}
    PayStatus -->|No| PayError[Show Payment Error]
    PayError --> Retry{Retry?}
    Retry -->|Yes| SelectMethod
    Retry -->|No| ReleaseLock[Release Slot Lock] --> Exit2([Exit])
    
    PayStatus -->|Yes| CreateBooking[Create Booking Record]
    CreateBooking --> SendConfirm[Send Confirmation]
    SendConfirm --> ShowConfirm[Display Confirmation]
    ShowConfirm --> Success([Booking Complete])
```

---

## 3. Booking Cancellation Flow

```mermaid
flowchart TD
    Start([Start]) --> MyBookings[View My Bookings]
    MyBookings --> SelectBooking[Select Booking]
    SelectBooking --> BookingDetails[View Booking Details]
    BookingDetails --> InitCancel[Click Cancel]
    
    InitCancel --> CanCancel{Cancellation Allowed?}
    CanCancel -->|No - Past| PastError[Cannot Cancel Past Booking] --> End1([End])
    CanCancel -->|No - Already| AlreadyError[Already Cancelled] --> End1
    
    CanCancel -->|Yes| ShowPolicy[Show Cancellation Policy]
    ShowPolicy --> CalcRefund[Calculate Refund Amount]
    CalcRefund --> DisplayRefund[Display Refund Info]
    
    DisplayRefund --> Confirm{Confirm Cancel?}
    Confirm -->|No| KeepBooking[Keep Booking] --> End2([End])
    Confirm -->|Yes| ProcessCancel[Process Cancellation]
    
    ProcessCancel --> UpdateStatus[Update Booking Status]
    UpdateStatus --> HasRefund{Refund Applicable?}
    
    HasRefund -->|Yes| ProcessRefund[Process Refund]
    ProcessRefund --> RefundStatus{Refund Success?}
    RefundStatus -->|No| ManualRefund[Queue for Manual] --> Notify
    RefundStatus -->|Yes| Notify[Send Notifications]
    
    HasRefund -->|No| Notify
    
    Notify --> ReleaseSlot[Release Slot to Availability]
    ReleaseSlot --> ShowCancel[Display Cancellation Confirmation]
    ShowCancel --> End3([Cancellation Complete])
```

---

## 4. Provider Resource Setup Flow

```mermaid
flowchart TD
    Start([Start]) --> ProviderLogin[Provider Login]
    ProviderLogin --> Dashboard[Provider Dashboard]
    Dashboard --> AddResource[Click Add Resource]
    
    AddResource --> BasicInfo[Enter Basic Info]
    BasicInfo -->|Name, Description, Category| ValidateBasic{Valid?}
    ValidateBasic -->|No| BasicError[Show Errors] --> BasicInfo
    ValidateBasic -->|Yes| UploadImages[Upload Images]
    
    UploadImages --> ValidateImages{Valid Images?}
    ValidateImages -->|No| ImageError[Show Image Errors] --> UploadImages
    ValidateImages -->|Yes| SetLocation[Set Location]
    
    SetLocation --> EnterAddress[Enter Address]
    EnterAddress --> Geocode[Geocode Address]
    Geocode --> ConfirmMap[Confirm on Map]
    ConfirmMap --> SetCapacity[Set Capacity & Amenities]
    
    SetCapacity --> SetPricing[Configure Pricing]
    SetPricing --> BasePrice[Set Base Price]
    BasePrice --> PeakOff{Add Peak/Off-Peak?}
    PeakOff -->|Yes| ConfigurePeak[Configure Time-Based Pricing]
    ConfigurePeak --> SetPricing
    PeakOff -->|No| SetAvailability[Configure Availability]
    
    SetAvailability --> WeeklySchedule[Set Weekly Schedule]
    WeeklySchedule --> SlotDuration[Set Slot Duration]
    SlotDuration --> BufferTime[Set Buffer Time]
    BufferTime --> SpecialDates{Add Special Dates?}
    SpecialDates -->|Yes| AddHolidays[Add Holidays/Closures]
    AddHolidays --> SetAvailability
    SpecialDates -->|No| Preview[Preview Resource]
    
    Preview --> Satisfied{Satisfied?}
    Satisfied -->|No| Edit[Edit Details] --> BasicInfo
    Satisfied -->|Yes| Submit[Submit for Review]
    
    Submit --> AutoApprove{Auto-Approve?}
    AutoApprove -->|Yes| Activate[Activate Resource]
    AutoApprove -->|No| PendingReview[Pending Admin Review]
    
    PendingReview --> AdminReview{Admin Decision}
    AdminReview -->|Approved| Activate
    AdminReview -->|Rejected| Rejected[Notify Rejection] --> End1([End])
    
    Activate --> GoLive[Resource Goes Live]
    GoLive --> End2([Resource Available])
```

---

## 5. Payment Processing Flow

```mermaid
flowchart TD
    Start([Payment Initiated]) --> BuildOrder[Build Order Summary]
    BuildOrder --> ShowSummary[Display Price Breakdown]
    ShowSummary --> SelectMethod{Select Payment Method}
    
    SelectMethod -->|Card| CardForm[Show Card Form]
    SelectMethod -->|Wallet| WalletRedirect[Redirect to Wallet]
    SelectMethod -->|UPI| UPIForm[Show UPI Form]
    SelectMethod -->|Saved| UseSaved[Use Saved Method]
    
    CardForm --> EnterCard[Enter Card Details]
    EnterCard --> ValidateCard{Card Valid?}
    ValidateCard -->|No| CardError[Show Error] --> CardForm
    ValidateCard -->|Yes| Tokenize[Tokenize Card]
    
    WalletRedirect --> WalletAuth[Authenticate in Wallet]
    WalletAuth --> WalletCallback[Return with Token]
    
    UPIForm --> EnterUPI[Enter UPI ID]
    EnterUPI --> ValidateUPI{UPI Valid?}
    ValidateUPI -->|No| UPIError[Show Error] --> UPIForm
    ValidateUPI -->|Yes| SendUPIRequest[Send Payment Request]
    
    UseSaved --> GetToken[Get Saved Token]
    
    Tokenize --> InitCharge[Initialize Charge]
    WalletCallback --> InitCharge
    SendUPIRequest --> WaitUPI[Wait for UPI Confirmation]
    GetToken --> InitCharge
    
    WaitUPI --> UPIStatus{UPI Status}
    UPIStatus -->|Timeout| UPITimeout[Payment Timeout] --> Fail
    UPIStatus -->|Declined| UPIDecline[Payment Declined] --> Fail
    UPIStatus -->|Success| PaySuccess
    
    InitCharge --> GatewayCall[Call Payment Gateway]
    GatewayCall --> GatewayResponse{Gateway Response}
    
    GatewayResponse -->|3DS Required| ThreeDS[Handle 3D Secure]
    ThreeDS --> ThreeDSResult{3DS Result}
    ThreeDSResult -->|Success| PaySuccess[Payment Successful]
    ThreeDSResult -->|Failed| Fail[Payment Failed]
    
    GatewayResponse -->|Approved| PaySuccess
    GatewayResponse -->|Declined| Fail
    GatewayResponse -->|Error| GatewayError[Gateway Error]
    GatewayError --> RetryGateway{Retry?}
    RetryGateway -->|Yes| GatewayCall
    RetryGateway -->|No| Fail
    
    Fail --> ShowError[Show Error Message]
    ShowError --> RetryPayment{Retry Payment?}
    RetryPayment -->|Yes| SelectMethod
    RetryPayment -->|No| Abandoned([Payment Abandoned])
    
    PaySuccess --> RecordTxn[Record Transaction]
    RecordTxn --> GenerateReceipt[Generate Receipt]
    GenerateReceipt --> SendReceipt[Email Receipt]
    SendReceipt --> Complete([Payment Complete])
```

---

## 6. Notification Dispatch Flow

```mermaid
flowchart TD
    Start([Event Triggered]) --> IdentifyEvent[Identify Event Type]
    IdentifyEvent --> GetRecipient[Get Recipient User]
    GetRecipient --> GetPrefs[Get User Preferences]
    
    GetPrefs --> CheckChannels{Enabled Channels}
    
    CheckChannels -->|Email| BuildEmail[Build Email Content]
    CheckChannels -->|SMS| BuildSMS[Build SMS Content]
    CheckChannels -->|Push| BuildPush[Build Push Content]
    
    BuildEmail --> SendEmail[Send via Email Provider]
    BuildSMS --> SendSMS[Send via SMS Provider]
    BuildPush --> SendPush[Send via Push Service]
    
    SendEmail --> EmailResult{Delivered?}
    SendSMS --> SMSResult{Delivered?}
    SendPush --> PushResult{Delivered?}
    
    EmailResult -->|Yes| LogEmail[Log Success]
    EmailResult -->|No| RetryEmail{Retry?}
    RetryEmail -->|Yes| SendEmail
    RetryEmail -->|No| FailEmail[Log Failure]
    
    SMSResult -->|Yes| LogSMS[Log Success]
    SMSResult -->|No| RetrySMS{Retry?}
    RetrySMS -->|Yes| SendSMS
    RetrySMS -->|No| FailSMS[Log Failure]
    
    PushResult -->|Yes| LogPush[Log Success]
    PushResult -->|No| RetryPush{Retry?}
    RetryPush -->|Yes| SendPush
    RetryPush -->|No| FailPush[Log Failure]
    
    LogEmail --> Complete
    LogSMS --> Complete
    LogPush --> Complete
    FailEmail --> Complete
    FailSMS --> Complete
    FailPush --> Complete([Notification Complete])
```
