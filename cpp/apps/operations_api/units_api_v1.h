#pragma once

#include <functional>

#include <drogon/HttpController.h>

namespace telemetry::api::v1 {

class UnitsController : public drogon::HttpController<UnitsController> {
public:
    METHOD_LIST_BEGIN
    ADD_METHOD_TO(UnitsController::get_units, "/api/v1/units", drogon::Get);
    ADD_METHOD_TO(UnitsController::get_units, "/api/v1/units", drogon::Options);
    METHOD_LIST_END

    static void get_units(
        const drogon::HttpRequestPtr& req,
        std::function<void(const drogon::HttpResponsePtr&)>&& callback);
};

}  // namespace telemetry::api::v1
