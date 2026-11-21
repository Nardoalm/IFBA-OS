/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <KRunner/AbstractRunner>
#include <KService>

class IfbaAppDescriptionRunner : public KRunner::AbstractRunner
{
    Q_OBJECT

public:
    IfbaAppDescriptionRunner(QObject *parent, const KPluginMetaData &metadata);

    void init() override;
    void match(KRunner::RunnerContext &context) override;
    void run(const KRunner::RunnerContext &context, const KRunner::QueryMatch &match) override;

private:
    void refreshServices();

    QList<KService::Ptr> m_services;
    bool m_matching = false;
};
