/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "appdescriptionrunner.h"

#include "descriptionmatcher.h"

#include <KApplicationTrader>
#include <KRunner/QueryMatch>
#include <KRunner/RunnerContext>
#include <KIO/ApplicationLauncherJob>
#include <KNotificationJobUiDelegate>
#include <KService>
#include <KSycoca>
#include <KLocalizedString>
#include <QUrl>
#include <utility>

IfbaAppDescriptionRunner::IfbaAppDescriptionRunner(QObject *parent, const KPluginMetaData &metadata)
    : KRunner::AbstractRunner(parent, metadata)
{
    addSyntax(QStringLiteral(":q:"), i18n("Find installed applications by description"));

    connect(this, &KRunner::AbstractRunner::prepare, this, [this]() {
        m_matching = true;
        if (m_services.isEmpty()) {
            refreshServices();
        } else {
            KSycoca::self()->ensureCacheValid();
        }
    });
    connect(this, &KRunner::AbstractRunner::teardown, this, [this]() {
        m_matching = false;
    });
}

void IfbaAppDescriptionRunner::init()
{
    connect(KSycoca::self(), &KSycoca::databaseChanged, this, [this]() {
        if (m_matching) {
            refreshServices();
        } else {
            m_services.clear();
        }
    });
}

void IfbaAppDescriptionRunner::refreshServices()
{
    m_services = KApplicationTrader::query([](const KService::Ptr &service) {
        return !service->noDisplay() && !service->comment().isEmpty();
    });
}

void IfbaAppDescriptionRunner::match(KRunner::RunnerContext &context)
{
    const QString query = context.query().simplified();
    if (query.size() < 2 || !context.isValid()) {
        return;
    }

    for (const KService::Ptr &service : std::as_const(m_services)) {
        if (!context.isValid()) {
            return;
        }
        if (!IfbaAppSearch::matchesDescription(service->comment(), query)) {
            continue;
        }

        KRunner::QueryMatch result(this);
        result.setText(service->name());
        result.setSubtext(service->comment());
        result.setIconName(service->icon());
        result.setId(QStringLiteral("ifba-description:%1").arg(service->storageId()));

        QUrl applicationUrl(service->storageId());
        applicationUrl.setScheme(QStringLiteral("applications"));
        result.setData(applicationUrl);
        result.setCategoryRelevance(KRunner::QueryMatch::CategoryRelevance::Moderate);
        result.setRelevance(0.4);
        context.addMatch(result);
    }
}

void IfbaAppDescriptionRunner::run(const KRunner::RunnerContext &, const KRunner::QueryMatch &match)
{
    const QUrl applicationUrl = match.data().toUrl();
    const KService::Ptr service = KService::serviceByStorageId(applicationUrl.path());
    if (!service) {
        return;
    }

    auto *job = new KIO::ApplicationLauncherJob(service);
    auto *delegate = new KNotificationJobUiDelegate;
    delegate->setAutoErrorHandlingEnabled(true);
    job->setUiDelegate(delegate);
    job->start();
}

K_PLUGIN_CLASS_WITH_JSON(IfbaAppDescriptionRunner, "ifba_app_description_runner.json")

#include "appdescriptionrunner.moc"
