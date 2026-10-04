# Value Object 設計・PHP実装例

## Value Object とは

- **値そのもの**を表すオブジェクト。ID（識別子）を持たない
- 同じ値を持つ2つのインスタンスは「等しい」とみなされる（値の同一性）
- **不変（Immutable）**: 一度生成されたら変更できない
- **自己検証**: コンストラクタでバリデーションを行い、不正な値を持つオブジェクトの生成を防ぐ

## 実装規約の目安（PHP の例）

```php
final readonly class <ClassName>
{
    public function __construct(
        public readonly <type> $value,
    ) {
        $this->validate();
    }

    private function validate(): void
    {
        // バリデーションロジック
        // 失敗時は例外をスロー
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

### ルール

- `final`: 継承を禁止する（Value Object は拡張されるべきではない）
- `readonly`: PHP 8.2+ の `readonly class` でプロパティの不変性を保証する
- コンストラクタでバリデーション、失敗時は `\InvalidArgumentException` またはカスタム例外

---

## 実装例1: 注文金額（OrderAmount）

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order;

final readonly class OrderAmount
{
    public function __construct(
        public readonly int $value,
    ) {
        if ($value < 0) {
            throw new \InvalidArgumentException(
                "注文金額は0以上である必要があります。value={$value}"
            );
        }
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function add(self $other): self
    {
        return new self($this->value + $other->value);
    }

    public function formatted(): string
    {
        return '¥' . number_format($this->value);
    }
}
```

### 使用例

```php
$amount = new OrderAmount(50000);
echo $amount->formatted(); // ¥50,000

$total = $amount->add(new OrderAmount(10000));
echo $total->formatted(); // ¥60,000

// 不正な値はコンストラクタで拒否
new OrderAmount(-1); // InvalidArgumentException
```

---

## 実装例2: 在庫数（StockQuantity）

```php
<?php

declare(strict_types=1);

namespace App\Domain\Product;

final readonly class StockQuantity
{
    private const int MIN_QUANTITY = 0;
    private const int MAX_QUANTITY = 99999;

    public function __construct(
        public readonly int $value,
    ) {
        if ($this->value < self::MIN_QUANTITY || $this->value > self::MAX_QUANTITY) {
            throw new \InvalidArgumentException(
                "在庫数は0〜{$this->maxQuantityLabel()}の範囲である必要があります。value={$this->value}"
            );
        }
    }

    public function decrease(int $amount): self
    {
        return new self($this->value - $amount);
    }

    public function isOutOfStock(): bool
    {
        return $this->value === 0;
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    private function maxQuantityLabel(): string
    {
        return (string) self::MAX_QUANTITY;
    }
}
```

---

## 実装例3: 注文ステータス（OrderStatus）

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order;

final readonly class OrderStatus
{
    private const array VALID_STATUSES = ['draft', 'confirmed', 'preparing', 'shipped', 'cancelled'];

    public function __construct(
        public readonly string $value,
    ) {
        if (!in_array($value, self::VALID_STATUSES, true)) {
            throw new \InvalidArgumentException(
                "不正なステータスです。value={$value}"
            );
        }
    }

    public static function draft(): self     { return new self('draft'); }
    public static function confirmed(): self { return new self('confirmed'); }
    public static function shipped(): self  { return new self('shipped'); }
    public static function cancelled(): self  { return new self('cancelled'); }

    public function isShipped(): bool { return $this->value === 'shipped'; }
    public function canTransitionTo(self $next): bool
    {
        $transitions = [
            'draft'        => ['confirmed'],
            'confirmed'    => ['preparing'],
            'preparing' => ['shipped', 'cancelled'],
            'shipped'     => [],
            'cancelled'     => [],
        ];
        return in_array($next->value, $transitions[$this->value], true);
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

---

## テストで確認する観点

- 正常な値で生成でき、保持した値が取り出せる
- 不正な値（境界値の外側を含む）で生成すると例外になる
- 演算（`add` など）が新しいインスタンスを返し、元のインスタンスは変わらない
- 同じ値のインスタンスは `equals()` で等しく、異なる値では等しくない
- 状態遷移を持つ場合、許可された遷移だけが `true` になる
