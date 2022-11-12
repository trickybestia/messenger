# Пакеты

## Register
```
type: "Register"
payload: {
    password: str
}
```

## RegisterSuccess
```
type: "RegisterSuccess"
payload: {
    id: Id
}
```

## Login
```
type: "Login"
payload: {
    id: Id
    password: str
}
```

## LoginSuccess
```
type: "LoginSuccess"
payload: None
```

## LoginFail
```
type: "LoginFail"
payload: None
```

## GetMessagesCount
```
type: "GetMessagesCount"
payload: None
```

## GetMessagesCountSuccess
```
type: "GetMessagesCountSuccess"
payload: {
    messages_count: int
}
```

## SendMessage
```
type: "SendMessage"
payload: {
    receiver_id: Id
    content: bytes
}
```

## SendMessageSuccess
```
type: "SendMessageSuccess"
payload: None
```

## SendMessageFailNoSuchClient
```
type: "SendMessageFailNoSuchClient"
payload: None
```

## GetMessages
```
type: "GetMessages"
payload: {
    first_message_index: int
    last_message_index: int
}
```

## GetMessagesSuccess
```
type: "GetMessagesSuccess"
payload: {
    messages: list[bytes]
}
```

## GetMessagesFailInvalidRange
```
type: "GetMessagesFailInvalidRange"
payload: None
```

## NewMessage
```
type: "NewMessage"
payload: {
    content: bytes
}
```
