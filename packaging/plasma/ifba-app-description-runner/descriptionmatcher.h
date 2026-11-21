/* SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include <QString>
#include <QStringList>
#include <Qt>

namespace IfbaAppSearch
{

inline bool matchesDescription(const QString &description, const QString &query)
{
    const QString normalizedDescription = description.simplified();
    const QStringList terms = query.simplified().split(QLatin1Char(' '), Qt::SkipEmptyParts);
    if (normalizedDescription.isEmpty() || terms.isEmpty()) {
        return false;
    }

    for (const QString &term : terms) {
        if (!normalizedDescription.contains(term, Qt::CaseInsensitive)) {
            return false;
        }
    }
    return true;
}

} // namespace IfbaAppDescriptionRunner
