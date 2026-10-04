# Repository パターン

## Repository パターンとは

- **ドメイン層**にインターフェースを定義し、**インフラ層**に実装を置く
- ドメインはデータの永続化方法（RDB / ファイル / 外部 API など）を知らない
- テスト時にインターフェースを別の実装（インメモリ実装やモック）に差し替えられる

## 配置

```
<ドメイン層>/Order/Repositories/OrderRepositoryInterface    ← インターフェース（ドメイン）
<インフラ層>/Repositories/<永続化手段>OrderRepository         ← 実装（インフラ）
```

ディレクトリ名・namespace はプロジェクトの規約に従う。以下のコードの namespace は説明用の例。

---

## Repository インターフェース（ドメイン層）

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Repositories;

use App\Domain\Order\Order;
use App\Domain\Order\OrderId;
use App\Domain\Customer\CustomerId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    /** @return Order[] */
    public function findByCustomer(CustomerId $customerId): array;

    public function save(Order $order): void;

    public function delete(OrderId $id): void;
}
```

### ルール

- `find*` メソッドはドメインの Entity / 値オブジェクトを返す（ORM のモデルや DB の行を返さない）
- `save()` は insert と update の両方を担う（差分は実装側で判断）
- `delete()` は ID を受け取る
- インターフェースには永続化手段の型（ORM のクラスなど）を持ち込まない

---

## Repository 実装（インフラ層）

実装は永続化手段（ORM、SQL、ファイル、外部 API など）ごとに書く。どの手段でも次を守る。

- 戻り値はドメインの型にする。永続化側の表現（DB の行、ORM のモデル）→ ドメインの変換（`toDomain` など）は実装の内側に閉じ込める
- ドメイン → 永続化側の変換（`save` 内）も実装の内側に閉じ込める
- 永続化側の型を、インターフェースの外（Service・Controller）へ漏らさない

永続化手段に依存しない最小の実装例として、インメモリ実装を示す。テストでの差し替えや、永続化を後回しにした開発初期にも使える。

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Repositories;

use App\Domain\Order\Order;
use App\Domain\Order\OrderId;
use App\Domain\Order\Repositories\OrderRepositoryInterface;
use App\Domain\Customer\CustomerId;

class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<int, Order> */
    private array $store = [];

    public function findById(OrderId $id): ?Order
    {
        return $this->store[$id->value] ?? null;
    }

    /** @return Order[] */
    public function findByCustomer(CustomerId $customerId): array
    {
        return array_values(array_filter(
            $this->store,
            fn(Order $order) => $order->customerId()->equals($customerId)
        ));
    }

    public function save(Order $order): void
    {
        $this->store[$order->id()->value] = $order;
    }

    public function delete(OrderId $id): void
    {
        unset($this->store[$id->value]);
    }
}
```

---

## 依存性注入

呼び出し側（ユースケース・Service）は、インターフェースにだけ依存する。具体的な実装クラスは、起動時の設定（DI コンテナや組み立て用コード）で差し込む。DI の設定方法はフレームワークごとに異なるので、プロジェクトの規約に従う。

```php
class OrderService
{
    public function __construct(
        private readonly OrderRepositoryInterface $repository,
    ) {}

    public function confirm(int $orderId): void
    {
        $order = $this->repository->findById(new OrderId($orderId));
        if ($order === null) {
            throw new \DomainException("注文が見つかりません。id={$orderId}");
        }
        $order->confirm();
        $this->repository->save($order);
    }
}
```

---

## テストで確認する観点

- ユースケース・Service のテストでは、インターフェースを満たすインメモリ実装またはモックに差し替える（永続化なしで業務ロジックを確認できる）
- 「見つかったら更新して保存する」「見つからなければ例外」のように、Repository の呼び出し方（取得 → 変更 → 保存）を確認する
- 実装クラス自体は、実際の永続化手段を使った結合テストで、保存した内容を取得し直して同じ値になることを確認する
