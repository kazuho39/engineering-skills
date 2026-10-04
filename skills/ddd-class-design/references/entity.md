# Entity 設計

## Entity とは

- **識別子（ID）を持つ**オブジェクト。同じ ID を持つ2つのオブジェクトは「同じエンティティ」とみなされる（識別子の同一性）
- **ライフサイクル**を持つ: 生成・変更・削除が起きる
- **状態を持つ**: 内部状態の変化を許容する（Value Object とは異なる）
- Value Object を積極的に活用して、プリミティブ型（string/int）の使い過ぎを避ける

## Value Object との違い

| 観点 | Value Object | Entity |
|------|-------------|--------|
| 同一性の基準 | 値（すべてのプロパティが等しければ同じ） | 識別子（IDが同じなら同じ） |
| 可変性 | 不変 | 可変（状態変化あり） |
| 例 | 注文金額・ステータス・在庫数 | 注文・商品・顧客 |

---

## 実装規約の目安（PHP の例）

```php
<?php

declare(strict_types=1);

namespace App\Domain\<Context>;

class <EntityName>
{
    private function __construct(
        private readonly <IdType> $id,
        private <StateType> $state,
        // 他のプロパティ（Value Object を使う）
    ) {}

    // ファクトリメソッドで生成
    public static function create(...): self
    {
        return new self(...);
    }

    public static function reconstruct(<IdType> $id, ...): self
    {
        return new self($id, ...);
    }

    // 状態変化はメソッドで表現
    public function <action>(): void
    {
        $this->state = $this->state->transitionTo(...);
    }

    public function id(): <IdType> { return $this->id; }
}
```

### ルール

- コンストラクタは `private` — 外部からの直接インスタンス化を禁止する
- `create()`: 新規作成（DB に保存前の新しいエンティティ）
- `reconstruct()`: 永続化層からの復元（DB から取得したデータの再構築）
- 状態変化は**メソッドで表現**し、直接プロパティを変更しない

---

## 実装例: 注文（Order）

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order;

use App\Domain\Customer\CustomerId;

class Order
{
    private function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private OrderStatus $status,
        private readonly \DateTimeImmutable $orderedAt,
    ) {}

    public static function create(
        OrderId $id,
        CustomerId $customerId,
    ): self {
        return new self(
            id: $id,
            customerId: $customerId,
            status: OrderStatus::draft(),
            orderedAt: new \DateTimeImmutable(),
        );
    }

    public static function reconstruct(
        OrderId $id,
        CustomerId $customerId,
        OrderStatus $status,
        \DateTimeImmutable $orderedAt,
    ): self {
        return new self($id, $customerId, $status, $orderedAt);
    }

    /** 注文を確定する */
    public function confirm(): void
    {
        $next = OrderStatus::confirmed();
        if (!$this->status->canTransitionTo($next)) {
            throw new \DomainException(
                "注文を確定できない状態です。current={$this->status->value}"
            );
        }
        $this->status = $next;
    }

    /** 発送準備を開始する */
    public function markPreparing(): void
    {
        $next = OrderStatus::preparing();
        if (!$this->status->canTransitionTo($next)) {
            throw new \DomainException(
                "発送準備を開始できない状態です。current={$this->status->value}"
            );
        }
        $this->status = $next;
    }

    public function id(): OrderId         { return $this->id; }
    public function customerId(): CustomerId    { return $this->customerId; }
    public function status(): OrderStatus { return $this->status; }
    public function orderedAt(): \DateTimeImmutable { return $this->orderedAt; }
}
```

---

## 状態遷移の設計パターン

Entity の状態遷移は以下の方法で設計する:

1. **Value Object としてのステータス**: `OrderStatus` のように `canTransitionTo()` を持たせる
2. **Entity のメソッド**: `confirm()`, `markPreparing()` など、意図を表すメソッドで状態変化を表現する
3. **不正遷移の防止**: 許可されていない遷移は `\DomainException` をスロー

```
draft → confirmed → preparing → shipped
                                 → cancelled
```

---

## テストで確認する観点

- `create()` で生成した直後の状態が期待どおりである（初期ステータスなど）
- 許可された状態遷移メソッドで、状態が期待どおりに変わる
- 許可されていない状態からの遷移は例外になる（不正遷移の防止）
- `reconstruct()` で任意の状態のエンティティを復元でき、遷移の前提条件を作れる
