.class public Lcom/android/vending/billing/InAppBillingServiceProxy;
.super Landroid/app/Service;
.source "InAppBillingServiceProxy.java"


# static fields
.field private static final TAG:Ljava/lang/String; = "IABProxy"


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Landroid/app/Service;-><init>()V

    return-void
.end method


# virtual methods
.method public onBind(Landroid/content/Intent;)Landroid/os/IBinder;
    .registers 5

    const-string v0, "IABProxy"
    const-string v1, "InAppBillingServiceProxy bound"

    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 20
    new-instance v0, Lcom/android/vending/billing/InAppBillingServiceProxy$Stub;

    invoke-direct {v0, p0}, Lcom/android/vending/billing/InAppBillingServiceProxy$Stub;-><init>(Lcom/android/vending/billing/InAppBillingServiceProxy;)V

    return-object v0
.end method