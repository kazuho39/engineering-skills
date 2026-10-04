# イミュータブル設計

一度作ったオブジェクトを変更せず、変更が必要なときは「変更後の値を持つ新しいオブジェクト」を返す設計。
契約による設計では、`readonly` で生成後の変更を禁止して不変条件が壊れないようにする。

※ コード例は PHP。他の言語では、同等の仕組み（`final` / `readonly` / `const` / 凍結オブジェクトなど）に読み替える。

## ミュータブルとイミュータブル

```php
// ミュータブル: 同じオブジェクトを書き換える
$account->withdraw(new Money(300));          // $account 自体が変わる

// イミュータブル: 新しいオブジェクトを返す
$newAccount = $account->withdraw(new Money(300));  // $account は不変のまま
```

```php
// イミュータブルな Money
final readonly class Money
{
    public function __construct(public int $amount)
    {
        if ($amount < 0) {
            throw new \InvalidArgumentException();
        }
    }

    public function add(Money $other): self
    {
        return new self($this->amount + $other->amount); // 新しいインスタンス
    }
}
```

## 副作用との関係

次はすべて副作用。副作用は隔離し、可能な限り純粋関数を設計する（[side-effects.md](side-effects.md)）。

- インスタンス変数の変更
- グローバル変数の変更
- 参照型引数の変更
- DB・ファイルなどの I/O

## 使い分けの目安

| 対象 | 方針 |
|---|---|
| 値オブジェクト | 完全に不変にする。変更は新インスタンスを返す |
| エンティティ | 状態遷移は許容する。ただし遷移メソッドごとに事前条件（今の状態から遷移できるか）をガード節で検証し、遷移後も不変条件を満たす |
| DTO | 不変にして、受け渡し中に変更されないようにする |
