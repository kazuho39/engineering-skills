# 副作用（Side Effect）

副作用とは、関数・メソッドが「戻り値を返す」以外に、外部の状態を変えたり、外部の状態に依存したりすること。
困る点は「予測できない」「テストしにくい」の2つ。

※ コード例は PHP。他の言語では読み替える。

## 具体例

| 種類 | 例 |
|---|---|
| 自分や引数の状態を書き換える | `$this->count++`、参照渡し引数 `array &$a` の変更 |
| グローバル・静的な状態を変更する | グローバル変数、`static` プロパティ、シングルトンの書き換え |
| 外部への出力・I/O | DB の INSERT/UPDATE、ファイル書き込み、API 呼び出し、メール送信、ログ出力 |
| 例外を投げる | 制御フローを変える（副作用に含める流儀と含めない流儀がある。このスキルでは、契約違反を知らせるガード節の例外は許容する） |
| 外部状態への依存 | `date()` / `now()`、`rand()`、DB の読み取り、環境変数 |

```php
// 副作用あり: 呼ぶたびに結果が変わる
public function addTax(): int
{
    $this->price = $this->price * 1.1;
    return $this->price;
}

// 純粋関数: 同じ入力なら常に同じ出力
public function withTax(int $price): int
{
    return (int) ($price * 1.1);
}
```

## 対策: 副作用を明確にする

| 手段 | 例 |
|---|---|
| 名前で示す | `save()` / `sendWelcomeMail()` / `registerUser()`（動詞で「何が起きるか」を表す） |
| 副作用を持つクラスを分ける | `OrderRepository`（DB）、`Mailer`（メール）に責務を切り出す |
| インターフェースで依存を明示する | コンストラクタで `Mailer` を受け取る。依存が見えるので副作用の有無が分かる |
| 計算と副作用を分離する | 計算は純粋関数、保存・送信は別メソッド |

```php
// 悪い: 名前は「計算」なのに DB 保存とメール送信が隠れている
public function calculateTotal(Order $order): int
{
    $total = ...;
    $this->db->save($order);     // 隠れた副作用
    $this->mailer->send(...);    // 隠れた副作用
    return $total;
}

// 良い: 計算は純粋、副作用は名前と責務で明示
public function calculateTotal(Order $order): Money { ... }

public function placeOrder(Order $order): void
{
    $total = $this->calculateTotal($order);   // 純粋
    $this->orders->save($order);              // 副作用（DB）
    $this->mailer->sendConfirmation($order);  // 副作用（メール）
}
```

## 隔離の原則

- 副作用を伴う処理は**薄いクラス**に閉じ込める（Repository, Mailer, Clock など）
- そのクラスには副作用の操作以外のロジックを書かない
- 時刻・乱数・ID採番は引数または注入で受け取る（純粋ロジックの中で `now()` を直接呼ばない）

## 置き場の例（レイヤード構成の場合）

プロジェクトに配置規約がなければ、次のように役割ごとに置き場を分ける。

| 副作用 | 置き場 |
|---|---|
| DB 読み書き | 永続化を担う層の Repository 実装（インターフェースは純粋ロジック側に置く） |
| 外部 API | 外部連携を担う層のクライアント |
| 業務ロジック（純粋） | ドメイン層（エンティティ / 値オブジェクト / ドメインサービス） |
| 純粋部分と副作用の呼び出し順の組み立て | アプリケーション層のユースケース |
