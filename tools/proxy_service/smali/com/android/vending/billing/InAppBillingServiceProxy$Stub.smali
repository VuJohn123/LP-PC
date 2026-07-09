.class public Lcom/android/vending/billing/InAppBillingServiceProxy$Stub;
.super Lcom/android/vending/billing/IInAppBillingService$Stub;
.source "InAppBillingServiceProxy.java"


# instance fields
.field final synthetic this$0:Lcom/android/vending/billing/InAppBillingServiceProxy;


# direct methods
.method constructor <init>(Lcom/android/vending/billing/InAppBillingServiceProxy;)V
    .registers 2

    iput-object p1, p0, Lcom/android/vending/billing/InAppBillingServiceProxy$Stub;->this$0:Lcom/android/vending/billing/InAppBillingServiceProxy;

    invoke-direct {p0}, Lcom/android/vending/billing/IInAppBillingService$Stub;-><init>()V

    return-void
.end method


# virtual methods
.method public getBuyIntent(ILjava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Landroid/os/Bundle;
    .registers 10

    const-string v0, "IABProxy"
    const-string v1, "getBuyIntent called - returning fake success"

    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 35
    new-instance v0, Landroid/os/Bundle;

    invoke-direct {v0}, Landroid/os/Bundle;-><init>()V

    const-string v1, "RESPONSE_CODE"

    const/4 v2, 0x0  # BILLING_RESPONSE_RESULT_OK

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putInt(Ljava/lang/String;I)V

    const-string v1, "BUY_INTENT"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putParcelable(Ljava/lang/String;Landroid/os/Parcelable;)V

    return-object v0
.end method

.method public getPurchases(ILjava/lang/String;Ljava/lang/String;Ljava/lang/String;)Landroid/os/Bundle;
    .registers 9

    const-string v0, "IABProxy"
    const-string v1, "getPurchases called - returning empty list"

    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 45
    new-instance v0, Landroid/os/Bundle;

    invoke-direct {v0}, Landroid/os/Bundle;-><init>()V

    const-string v1, "RESPONSE_CODE"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putInt(Ljava/lang/String;I)V

    const-string v1, "INAPP_PURCHASE_ITEM_LIST"

    .line 48
    new-instance v2, Ljava/util/ArrayList;

    invoke-direct {v2}, Ljava/util/ArrayList;-><init>()V

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putStringArrayList(Ljava/lang/String;Ljava/util/ArrayList;)V

    const-string v1, "INAPP_PURCHASE_DATA_LIST"

    .line 49
    new-instance v2, Ljava/util/ArrayList;

    invoke-direct {v2}, Ljava/util/ArrayList;-><init>()V

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putStringArrayList(Ljava/lang/String;Ljava/util/ArrayList;)V

    const-string v1, "INAPP_DATA_SIGNATURE_LIST"

    .line 50
    new-instance v2, Ljava/util/ArrayList;

    invoke-direct {v2}, Ljava/util/ArrayList;-><init>()V

    invoke-virtual {v0, v1, v2}, Landroid/os/Bundle;->putStringArrayList(Ljava/lang/String;Ljava/util/ArrayList;)V

    return-object v0
.end method

.method public isBillingSupported(ILjava/lang/String;Ljava/lang/String;)I
    .registers 5

    const/4 v0, 0x0  # BILLING_RESPONSE_RESULT_OK

    return v0
.end method