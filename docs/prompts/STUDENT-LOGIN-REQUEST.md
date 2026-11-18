# Student greeting and login request

Original user request, preserved for implementation after the native XFCE modernization:

> em vez de Boa noite, coloque: Olá, (nome ou estudante)! e quando ligar o SO, deve pedir para o estudante logar com matricula e a senha (se for a primeira vez, deve ir com a senha padrao (12345) e deve pedir p mudar a senha

The shared `12345` bootstrap credential is not safe for a multi-user system. See `../IMPLEMENTATION-QUEUE.md`: implement per-user local accounts only through a real account-provisioning flow, and do not ship a shared password in the live ISO.
